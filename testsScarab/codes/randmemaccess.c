#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ARRAY_SIZE 40000000
#define STRIDE 4

int main() {
    int *array = (int *)malloc(sizeof(int) * ARRAY_SIZE);
    if (!array) {
        printf("Memory allocation failed!\n");
        return 1;
    }

    // Initialize array with random values
    srand(time(NULL));
    for (int i = 0; i < ARRAY_SIZE; i++) {
        array[rand() % ARRAY_SIZE] = rand() % 100;
    }

    // Access elements to simulate cache hit/miss behavior
    long sum = 0;
    for (int i = 0; i < ARRAY_SIZE; i += STRIDE) {
        sum += array[rand() % ARRAY_SIZE];
    }

    //printf("Sum of array elements: %ld\n", sum);
    free(array);

    return 0;
}
