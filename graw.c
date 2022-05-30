
#include <assert.h>
#include <curl/curl.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <uv.h>

#include "parson.h"

#define GITHUB_RAW_FORMAT "https://raw.githubusercontent.com/%s/%s/%s/%s/%s"
#define GITHUB_API_FORMAT "https://api.github.com/repos/%s/%s/git/trees/%s:%s?recursive=true"

// "https://api.github.com/repos/numToStr/dotfiles/git/trees/master:neovim/.config?recursive=true"

typedef struct URLData {
  char *username;
  char *repo;
  char *branch;
  char *directly;
} URLData;

struct GithubData {
  char *data;
  size_t size;
};

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp)
{
  size_t realsize = size * nmemb;
  struct GithubData *mem = (struct GithubData *)userp;

  char *ptr = realloc(mem->data, mem->size + realsize + 1);
  if (!ptr) {
    /* out of memory! */
    printf("not enough memory (realloc returned NULL)\n");
    return 0;
  }

  mem->data = ptr;
  memcpy(&(mem->data[mem->size]), contents, realsize);
  mem->size += realsize;
  mem->data[mem->size] = 0;

  return realsize;
}

uv_loop_t *loop;
CURLM *curl_handle;
uv_timer_t timeout;

typedef struct curl_context_s {
  uv_poll_t poll_handle;
  curl_socket_t sockfd;
} curl_context_t;

curl_context_t *create_curl_context(curl_socket_t sockfd)
{
  curl_context_t *context;

  context = (curl_context_t *)malloc(sizeof *context);

  context->sockfd = sockfd;

  int r = uv_poll_init_socket(loop, &context->poll_handle, sockfd);
  assert(r == 0);
  context->poll_handle.data = context;

  return context;
}

void curl_close_cb(uv_handle_t *handle)
{
  curl_context_t *context = (curl_context_t *)handle->data;
  free(context);
}

void destroy_curl_context(curl_context_t *context)
{
  uv_close((uv_handle_t *)&context->poll_handle, curl_close_cb);
}

void add_download(const char *url, int num)
{
  const char *filename = basename((char *)url);
  FILE *file;

  file = fopen(filename, "w");
  if (file == NULL) {
    fprintf(stderr, "Error opening %s\n", filename);
    return;
  }

  CURL *handle = curl_easy_init();
  curl_easy_setopt(handle, CURLOPT_WRITEDATA, file);
  curl_easy_setopt(handle, CURLOPT_URL, url);
  curl_multi_add_handle(curl_handle, handle);
  fprintf(stderr, "Added download %s -> %s\n", url, filename);
}

void check_multi_info(void)
{
  char *done_url;
  CURLMsg *message;
  int pending;

  while ((message = curl_multi_info_read(curl_handle, &pending))) {
    switch (message->msg) {
    case CURLMSG_DONE:
      curl_easy_getinfo(message->easy_handle, CURLINFO_EFFECTIVE_URL, &done_url);
      // printf("%s DONE\n", done_url);

      curl_multi_remove_handle(curl_handle, message->easy_handle);
      curl_easy_cleanup(message->easy_handle);
      break;

    default:
      fprintf(stderr, "CURLMSG default\n");
      abort();
    }
  }
}

void curl_perform(uv_poll_t *req, int status, int events)
{
  uv_timer_stop(&timeout);
  int running_handles;
  int flags = 0;
  if (status < 0)
    flags = CURL_CSELECT_ERR;
  if (!status && events & UV_READABLE)
    flags |= CURL_CSELECT_IN;
  if (!status && events & UV_WRITABLE)
    flags |= CURL_CSELECT_OUT;

  curl_context_t *context;

  context = (curl_context_t *)req;

  curl_multi_socket_action(curl_handle, context->sockfd, flags, &running_handles);
  check_multi_info();
}

void on_timeout(uv_timer_t *req)
{
  int running_handles;
  curl_multi_socket_action(curl_handle, CURL_SOCKET_TIMEOUT, 0, &running_handles);
  check_multi_info();
}

void start_timeout(CURLM *multi, long timeout_ms, void *userp)
{
  if (timeout_ms <= 0)
    /* 0 means directly call socket_action, but we'll do it in a bit */
    timeout_ms = 1;
  uv_timer_start(&timeout, on_timeout, timeout_ms, 0);
}

int handle_socket(CURL *easy, curl_socket_t s, int action, void *userp, void *socketp)
{
  curl_context_t *curl_context;
  if (action == CURL_POLL_IN || action == CURL_POLL_OUT) {
    if (socketp) {
      curl_context = (curl_context_t *)socketp;
    } else {
      curl_context = create_curl_context(s);
      curl_multi_assign(curl_handle, s, (void *)curl_context);
    }
  }

  switch (action) {
  case CURL_POLL_IN:
    uv_poll_start(&curl_context->poll_handle, UV_READABLE, curl_perform);
    break;
  case CURL_POLL_OUT:
    uv_poll_start(&curl_context->poll_handle, UV_WRITABLE, curl_perform);
    break;
  case CURL_POLL_REMOVE:
    if (socketp) {
      uv_poll_stop(&((curl_context_t *)socketp)->poll_handle);
      destroy_curl_context((curl_context_t *)socketp);
      curl_multi_assign(curl_handle, s, NULL);
    }
    break;
  default:
    abort();
  }

  return 0;
}

// check if given url is valid
int valid_github_url(char *url)
{
  return 0;
}

URLData get_url_data(char *url){

  const int URL_SIZE = (strlen(url) * 8) + 0;
  char *target_url = malloc(URL_SIZE);
  strcpy(target_url, url);

  const char *delim = "/";
  char **tokens_list = malloc(URL_SIZE);

  int count = 0;
  char *tokens = strtok(target_url, delim);

  while (tokens != NULL) {
    tokens = strtok(NULL, delim);
    tokens_list[count] = tokens;
    count++;
  }

  // debug
  for (int i = 0; i < count; i++) {
    printf("%d - %s\n", i, tokens_list[i]);
  }

  printf("url is = %s\n", url);
  printf("size is = %u\n", URL_SIZE);
  char *directly = malloc(URL_SIZE);
  for (int i = 0; i < count ; i++) {
    printf("%s\n", directly);
    strcat(directly, tokens_list[i]);
    strcat(directly, "/");
  }

  URLData data = {
    .username = tokens_list[1],
    .repo = tokens_list[2],
    .branch = tokens_list[4],
    .directly = directly,
  };

  printf("%s-%s-%s-%s", tokens_list[1], tokens_list[2], tokens_list[4], directly);

  free(tokens_list);
  return data;
}

int tree(char *url)
{
  if (valid_github_url(url) != 0) {
    fprintf(stderr, "Github : url is not valid\n");
    exit(1);
  }

  printf("%s\n", url);
  URLData url_data = get_url_data(url);

  CURL *handle;
  CURLcode res;

  struct GithubData chunk;

  chunk.data = malloc(1); /* will be grown as needed by the realloc above */
  chunk.size = 0;         /* no data at this point */

  // TODO: use GITHUB_API_FORMAT to make specific api link for subtree
  // TODO: make api call and parse the json respones

  // header list
  struct curl_slist *list = NULL;
  list = curl_slist_append(list, "Accept: application/vnd.github.v3+json");

  // curl_global_init(CURL_GLOBAL_ALL);

  handle = curl_easy_init();
  curl_easy_setopt(handle, CURLOPT_URL, url);
  curl_easy_setopt(handle, CURLOPT_HTTPHEADER, list);
  curl_easy_setopt(handle, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
  curl_easy_setopt(handle, CURLOPT_WRITEDATA, (void *)&chunk);
  curl_easy_setopt(handle, CURLOPT_USERAGENT, "libcurl/7.69.1");

  res = curl_easy_perform(handle);

  printf("%s\n", url);
  if (res != CURLE_OK) {
    fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
  } else {
    JSON_Value *root_value = json_parse_string(chunk.data);
    JSON_Object *tree_value = json_value_get_object(root_value);

    JSON_Array *directory = json_object_get_array(tree_value, "tree");
    JSON_Object *item;

    // printf("%s\n", chunk.data);
    // printf("%lu\n", chunk.size);
    // if (json_value_get_type(root_value) != JSONArray) {
    //   printf("%i\n", json_value_get_type(root_value));
    // }

    // printf("%-10.10s %-10.10s %s\n", "Date", "SHA", "Author");
    for (size_t i = 0; i < json_array_get_count(directory); i++) {
      item = json_array_get_object(directory, i);

      if (strcmp(json_object_dotget_string(item, "type"), "blob") == 0) {
        char *url = (char *)malloc(100 * sizeof(char));
        sprintf(url,
                GITHUB_RAW_FORMAT,
                url_data.username,
                url_data.repo,
                url_data.branch,
                url_data.directly,
                json_object_dotget_string(item, "path"));
        printf("%s", url);
        add_download(url, i);
      }

      // printf("%s %s\n", json_object_dotget_string(file, "path"),
      //        json_object_dotget_string(file, "type"));
    }
    json_value_free(root_value);
  }
  /* cleanup code */
  curl_slist_free_all(list); /* free the list again */
  // printf("API data:\n%s", handle);
  return 0;
}

int main(int argc, char **argv)
{
  loop = uv_default_loop();

  if (argc <= 1)
    return 0;

  if (curl_global_init(CURL_GLOBAL_ALL)) {
    fprintf(stderr, "Could not init cURL\n");
    return 1;
  }

  uv_timer_init(loop, &timeout);

  curl_handle = curl_multi_init();
  curl_multi_setopt(curl_handle, CURLMOPT_SOCKETFUNCTION, handle_socket);
  curl_multi_setopt(curl_handle, CURLMOPT_TIMERFUNCTION, start_timeout);

  if (tree(argv[1]) != 0) {
    exit(1);
  }

  while (argc-- > 1) {
    add_download(argv[argc], argc);
  }

  uv_run(loop, UV_RUN_DEFAULT);
  curl_multi_cleanup(curl_handle);
  return 0;
}

// vim: sw=2
