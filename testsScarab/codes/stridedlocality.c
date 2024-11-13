#include <stdio.h>
#include <stdlib.h>
#define SIZE 100000000
#define STRIDE 10

int main() {
    int *array = (int*)malloc(SIZE * sizeof(int));
    if (array == NULL) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    // Initialize array
    for (int i = 0; i < SIZE; i++) {
        array[i] = i;
    }

    int sum = 0;
    // Access elements with a stride
    for (int i = 0; i < SIZE; i += STRIDE) {
        sum += array[i];
    }

    //printf("Sum: %d\n", sum);
    return 0;
}
