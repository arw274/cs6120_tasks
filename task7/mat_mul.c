#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 1000  // Matrix size: N x N

// Function to get current time in seconds (high precision)
double now() {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

// Basic O(N^3) matrix multiplication
void matmul(int A[N][N], int B[N][N], int C[N][N]) {
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            int sum = 0.0;
            for (int k = 0; k < N; ++k) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}

int main() {
    static int A[N][N], B[N][N], C[N][N];

    // Seed RNG
    srand(42);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            A[i][j] = rand();
            B[i][j] = rand();
        }
    }

    double start = now();

    matmul(A, B, C);

    double end = now();
    double elapsed = end - start;

    printf("Matrix size: %dx%d\n", N, N);
    printf("Elapsed time: %.8f seconds\n", elapsed);
    printf("C[0][0] = %.3d\n", C[0][0]);  // Print one element to prevent optimization

    return 0;
}