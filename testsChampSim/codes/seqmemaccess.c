#include <stdio.h>
#include <stdlib.h>

#define ARRAY_SIZE 100000000

int main() {
    int *array = (int *)malloc(sizeof(int) * ARRAY_SIZE);
    if (!array) {
        printf("Memory allocation failed!\n");
        return 1;
    }

    // Initialize array with random values
    for (int i = 0; i < ARRAY_SIZE; i++) {
        array[i] = rand() % 100;
    }

    // Sequential access pattern
    long long sum = 0;
    for (int i = 0; i < ARRAY_SIZE; i++) {
        sum += array[i];
    }

    // printf("Sum: %lld\n", sum);

    free(array);
    return 0;
}
