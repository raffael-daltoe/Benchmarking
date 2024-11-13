#include <stdio.h>
#define SIZE 100000000

int main() {
    int global_value = 0;
    int local_sum = 0;
    
    // Repeated access to different variables (hierarchical data)
    for (int i = 0; i < SIZE; i++) {
        global_value += 1;
        local_sum += global_value;
    }

    //printf("Global Value: %d, Local Sum: %d\n", global_value, local_sum);
    return 0;
}
