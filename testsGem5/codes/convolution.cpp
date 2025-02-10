#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define INPUT_SIZE 100000
#define KERNEL_SIZE 5
#define STRIDE 2
#define OUTPUT_SIZE ((INPUT_SIZE - KERNEL_SIZE) / STRIDE + 1)

// Activation function (ReLU)
float relu(float x) {
    return x > 0 ? x : 0;
}

// Perform convolution operation
void convolution(float **input, float **kernel, float **output) {
    for (int i = 0; i < OUTPUT_SIZE; i++) {
        for (int j = 0; j < OUTPUT_SIZE; j++) {
            float sum = 0;
            for (int ki = 0; ki < KERNEL_SIZE; ki++) {
                for (int kj = 0; kj < KERNEL_SIZE; kj++) {
                    sum += input[i * STRIDE + ki][j * STRIDE + kj] * kernel[ki][kj];
                }
            }
            output[i][j] = relu(sum);  // Apply activation function
        }
    }
}

// Allocate a 2D matrix
float **allocate_matrix(int rows, int cols) {
    float **matrix = (float **)malloc(rows * sizeof(float *));
    for (int i = 0; i < rows; i++) {
        matrix[i] = (float *)malloc(cols * sizeof(float));
    }
    return matrix;
}

// Free a 2D matrix
void free_matrix(float **matrix, int rows) {
    for (int i = 0; i < rows; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

// Initialize a 2D matrix with random values
void initialize_matrix(float **matrix, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i][j] = (float)(rand() % 100) / 100.0;  // Random values between 0 and 1
        }
    }
}

int main() {
    srand(time(NULL));

    // Allocate and initialize input, kernel, and output matrices
    float **input = allocate_matrix(INPUT_SIZE, INPUT_SIZE);
    float **kernel = allocate_matrix(KERNEL_SIZE, KERNEL_SIZE);
    float **output = allocate_matrix(OUTPUT_SIZE, OUTPUT_SIZE);

    initialize_matrix(input, INPUT_SIZE, INPUT_SIZE);
    initialize_matrix(kernel, KERNEL_SIZE, KERNEL_SIZE);

    // Perform convolution
    convolution(input, kernel, output);

    // Free allocated memory
    free_matrix(input, INPUT_SIZE);
    free_matrix(kernel, KERNEL_SIZE);
    free_matrix(output, OUTPUT_SIZE);

    return 0;
}
