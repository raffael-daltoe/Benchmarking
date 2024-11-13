#include <stdio.h>
#define SIZE 100000000

int main() {
    int value = 0;

    // Access the same variable multiple times
    for (int i = 0; i < SIZE; i++) {
        value += 1;
    }

    //printf("Value: %d\n", value);
    return 0;
}
