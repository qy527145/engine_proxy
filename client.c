#include <netinet/in.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>

int fd;

void *read_command(void *arg)
{
    char cmd[100];
    int len;
    while (1)
    {
        len = scanf("%s", cmd);
        send(fd, cmd, strlen(cmd), 0);
        send(fd, "\n", 1, 0);
        if (strcmp("quit", cmd) == 0)
        {
            close(fd);
            break;
        }
    }
    return NULL;
}
int main()
{
    char host[30] = "127.0.0.1";
    int port = 1717;
    FILE *fp = fopen("client.conf", "r");
    if (fp)
    {
        fscanf(fp, "%s %d", host, &port);
        fclose(fp);
    }
    else
    {
        fp = fopen("client.conf", "w");
        fprintf(fp, "%s %d", host, port);
        fclose(fp);
    }
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;

    // inet_pton(AF_INET,"127.0.0.1",&addr.sin_addr);
    inet_pton(AF_INET, host, &addr.sin_addr);
    // addr.sin_port = htons(1717);
    addr.sin_port = htons(port);
    fd = socket(AF_INET, SOCK_STREAM, 0);
    connect(fd, (struct sockaddr *)&addr, sizeof(addr));

    pthread_t t;
    pthread_create(&t, NULL, read_command, NULL);
    char buf;
    while (recv(fd, &buf, 1, 0) > 0)
    {
        printf("%c", buf);
    }
    return 0;
}
