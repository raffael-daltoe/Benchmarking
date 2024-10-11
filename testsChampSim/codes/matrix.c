#include <stdio.h>
#include <stdlib.h>

#define SIZE 50

void matrix_multiplication(int **mat1, int **mat2, int **result) {
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            result[i][j] = 0;
            for (int k = 0; k < SIZE; k++) {
                result[i][j] += mat1[i][k] * mat2[k][j];
            }
        }
    }
}

int main() {
    // Allocate memory for matrices using calloc to initialize all elements to 0
    int **mat1 = (int **)malloc(SIZE * sizeof(int *));
    int **mat2 = (int **)malloc(SIZE * sizeof(int *));
    int **result = (int **)malloc(SIZE * sizeof(int *));
    
    for (int i = 0; i < SIZE; i++) {
        mat1[i] = (int *)calloc(SIZE, sizeof(int));
        mat2[i] = (int *)calloc(SIZE, sizeof(int));
        result[i] = (int *)calloc(SIZE, sizeof(int));
    }

    // Initialize mat1 and mat2 with random values
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            mat1[i][j] = rand() % 100;
            mat2[i][j] = rand() % 100;
        }
    }

    // Perform matrix multiplication
    matrix_multiplication(mat1, mat2, result);

    printf("Matrix multiplication completed.\n");

    // Free allocated memory
    for (int i = 0; i < SIZE; i++) {
        free(mat1[i]);
        free(mat2[i]);
        free(result[i]);
    }
    free(mat1);
    free(mat2);
    free(result);

    return 0;
}