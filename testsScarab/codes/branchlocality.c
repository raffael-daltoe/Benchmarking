#include <stdio.h>
#include <stdlib.h>
#define SIZE 100000000

int main() {
    int *array = (int*)malloc(SIZE * sizeof(int));
    if (array == NULL) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    // Initialize array
    for (int i = 0; i < SIZE; i++) {
        int tmp = i;
        array[i] = tmp % 2 == 0 ? tmp : -tmp;
    }

    int sum = 0;
    // Branch-dependent access within a loop
    for (int i = 0; i < SIZE; i++) {
        if (array[i] >= 0) {
            sum += array[i];
        } else {
            sum -= array[i];
        }
    }

    free(array); // Free allocated memory
    return 0;
}
