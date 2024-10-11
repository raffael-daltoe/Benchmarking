#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define DIM1 200
#define DIM2 200
#define DIM3 200
#define OPERATIONS 1000000

int main() {
    // Allocate memory for the 3D matrix
    int ***matrix = (int ***)malloc(DIM1 * sizeof(int **));
    for (int i = 0; i < DIM1; i++) {
        matrix[i] = (int **)malloc(DIM2 * sizeof(int *));
        for (int j = 0; j < DIM2; j++) {
            matrix[i][j] = (int *)malloc(DIM3 * sizeof(int));
        }
    }

    // Initialize the matrix with random values
    srand(time(NULL));
    for (int i = 0; i < DIM1; i++) {
        for (int j = 0; j < DIM2; j++) {
            for (int k = 0; k < DIM3; k++) {
                matrix[i][j][k] = rand() % 100;
            }
        }
    }

    // Perform random access and modify a random position
    for (int i = 0; i < OPERATIONS; i++) {
        int x1 = rand() % DIM1;
        int y1 = rand() % DIM2;
        int z1 = rand() % DIM3;

        int x2 = rand() % DIM1;
        int y2 = rand() % DIM2;
        int z2 = rand() % DIM3;

        // Add value from one random position to another random position
        matrix[x2][y2][z2] += matrix[x1][y1][z1];
    }

    printf("Random operations on the 3D matrix completed.\n");

    // Free allocated memory
    for (int i = 0; i < DIM1; i++) {
        for (int j = 0; j < DIM2; j++) {
            free(matrix[i][j]);
        }
        free(matrix[i]);
    }
    free(matrix);

    return 0;
}
