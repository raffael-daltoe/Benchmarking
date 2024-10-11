#include <stdio.h>
#include <stdlib.h>

#define SIZE 1000

void transpose_matrix(int **matrix, int **transpose) {
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            transpose[j][i] = matrix[i][j];
        }
    }
}

int main() {
    // Allocate memory for matrices
    int **matrix = (int **)malloc(SIZE * sizeof(int *));
    int **transpose = (int **)malloc(SIZE * sizeof(int *));
    for (int i = 0; i < SIZE; i++) {
        matrix[i] = (int *)malloc(SIZE * sizeof(int));
        transpose[i] = (int *)malloc(SIZE * sizeof(int));
    }

    // Initialize matrix with random values
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            matrix[i][j] = rand() % 100;
        }
    }

    // Perform matrix transposition
    transpose_matrix(matrix, transpose);

    // Free allocated memory
    for (int i = 0; i < SIZE; i++) {
        free(matrix[i]);
        free(transpose[i]);
    }
    free(matrix);
    free(transpose);

    return 0;
}
