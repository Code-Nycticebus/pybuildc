#include <stdio.h>

#include "module/test.h"

int main(void) {
  printf("Hello\n");
  printf("a = %d\n", get_a());
  return 0;
}
