#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <pthread.h>

#define PORT 5000
#define BUFFER_SIZE 2048
#define MAX_CLIENTS 100

typedef struct {
    int socket;
    char id[BUFFER_SIZE];
} ClientInfo;

ClientInfo clients[MAX_CLIENTS];
int client_count = 0;
pthread_mutex_t clients_mutex = PTHREAD_MUTEX_INITIALIZER;

void send_to_client_by_id(const char* target_id, const char* message) {
    pthread_mutex_lock(&clients_mutex);
    for (int i = 0; i < client_count; ++i) {
        if (strcmp(clients[i].id, target_id) == 0) {
            ssize_t sent_bytes = write(clients[i].socket, message, strlen(message));
            if (sent_bytes <= 0) {
    printf("❌ [%s]에게 메시지 전송 실패\n", target_id);
}
                printf("📤 [%s] 에게 메시지 전송: %s\n", target_id, message);
                break;
            }
    }
    pthread_mutex_unlock(&clients_mutex);
}

void* handle_client(void* arg) {
    int client_socket = *(int*)arg;
    free(arg);

    char buffer[BUFFER_SIZE];
    memset(buffer, 0, BUFFER_SIZE);

    // 클라이언트 ID 수신
    ssize_t bytes = read(client_socket, buffer, BUFFER_SIZE);
    if (bytes <= 0) {
        printf("클라이언트 인증 수신 실패\n");
        close(client_socket);
        return NULL;
    }
    buffer[strcspn(buffer, "\r\n")] = 0;  // 줄바꿈 제거
    printf("클라이언트 접속됨 (ID: %s)\n", buffer);

    // 클라이언트 목록에 저장
    pthread_mutex_lock(&clients_mutex);
    if (client_count < MAX_CLIENTS) {
        clients[client_count].socket = client_socket;
        strncpy(clients[client_count].id, buffer, BUFFER_SIZE);
        client_count++;
    }
    pthread_mutex_unlock(&clients_mutex);

    // 인증 응답 전송
    const char* response = "인증 성공";
    ssize_t sent = write(client_socket, response, strlen(response));
    if (sent <= 0) {
        printf("클라이언트에게 응답 전송 실패\n");
        close(client_socket);
        return NULL;
    }

    while (1) {
        memset(buffer, 0, BUFFER_SIZE);
        ssize_t bytes_received = read(client_socket, buffer, BUFFER_SIZE);
        if (bytes_received <= 0) {
            printf("클라이언트 연결 종료\n");
            break;
        }

        buffer[strcspn(buffer, "\r\n")] = 0;
        printf("수신된 메시지: %s\n", buffer);

        if (strcmp(buffer, "아이몬") == 0) {
            printf("아이몬 이벤트 감지됨!\n");
            send_to_client_by_id("KJH", "아이몬");
        }

        if (strcmp(buffer, "무궁화") == 0) {
            printf("🌸 무궁화 이벤트 감지됨!\n");
            send_to_client_by_id("KJH", "무궁화");
        }
        else if (strcmp(buffer, "Game Over") == 0) {
            printf("게임 오버 이벤트 감지됨!\n");
            send_to_client_by_id("Jong", "게임 오버");
        }

        if (strcmp(buffer, "exit") == 0) {
            printf("클라이언트가 종료 요청함.\n");
            break;
        }
    }

    close(client_socket);

    // 연결 종료된 클라이언트를 목록에서 제거
    pthread_mutex_lock(&clients_mutex);
    for (int i = 0; i < client_count; ++i) {
        if (clients[i].socket == client_socket) {
            // 뒤에 있는 클라이언트를 앞으로 당김
            for (int j = i; j < client_count - 1; ++j) {
                clients[j] = clients[j + 1];
            }
            client_count--;
            break;
        }
    }
    pthread_mutex_unlock(&clients_mutex);

    return NULL;
}

int main() {
    int server_socket, *client_socket;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);

    server_socket = socket(AF_INET, SOCK_STREAM, 0);

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = INADDR_ANY;

    bind(server_socket, (struct sockaddr*)&server_addr, sizeof(server_addr));
    listen(server_socket, 5);

    printf("서버 시작. 포트: %d\n", PORT);

    while (1) {
        client_socket = malloc(sizeof(int));
        *client_socket = accept(server_socket, (struct sockaddr*)&client_addr, &client_len);
        pthread_t thread_id;
        pthread_create(&thread_id, NULL, handle_client, client_socket);
        pthread_detach(thread_id);
    }

    close(server_socket);
    return 0;
}
