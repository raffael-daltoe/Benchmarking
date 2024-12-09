#include <iostream>
#include <cstdlib>
#include <ctime>
#include <cmath>

#define SIZE 100000000 // Define the size of the list

struct Node {
    int value;
    Node* next;
};

// Function to create a linked list with random values
Node* create_list(int size) {
    Node* head = new Node{rand() % 1000 + 1, nullptr}; // Random value between 1 and 1000
    Node* current = head;
    for (int i = 1; i < size; ++i) {
        current->next = new Node{rand() % 1000 + 1, nullptr};
        current = current->next;
    }
    return head;
}

// Function to check if a number is prime
bool is_prime(int num) {
    if (num <= 1) return false;
    for (int i = 2; i <= std::sqrt(num); ++i) {
        if (num % i == 0) return false;
    }
    return true;
}

// Function to separate primes and non-primes into two lists
void separate_primes(Node* original, Node*& primes, Node*& non_primes, int& prime_count, int& non_prime_count) {
    prime_count = 0;
    non_prime_count = 0;
    Node* prime_tail = nullptr;
    Node* non_prime_tail = nullptr;

    while (original) {
        if (is_prime(original->value)) {
            ++prime_count;
            if (!primes) {
                primes = new Node{original->value, nullptr};
                prime_tail = primes;
            } else {
                prime_tail->next = new Node{original->value, nullptr};
                prime_tail = prime_tail->next;
            }
        } else {
            ++non_prime_count;
            if (!non_primes) {
                non_primes = new Node{original->value, nullptr};
                non_prime_tail = non_primes;
            } else {
                non_prime_tail->next = new Node{original->value, nullptr};
                non_prime_tail = non_prime_tail->next;
            }
        }
        original = original->next;
    }
}

// Function to calculate the average value of a list
double calculate_average(Node* list) {
    int sum = 0, count = 0;
    while (list) {
        sum += list->value;
        ++count;
        list = list->next;
    }
    return count ? static_cast<double>(sum) / count : 0.0;
}

// Function to free a linked list
void free_list(Node* list) {
    while (list) {
        Node* temp = list;
        list = list->next;
        delete temp;
    }
}

// Function to print a linked list
void print_list(Node* list) {
    while (list) {
        std::cout << list->value << " ";
        list = list->next;
    }
    std::cout << std::endl;
}

// Main function
int main() {
    srand(time(0)); // Seed for random numbers

    // Create the original list
    Node* original = create_list(SIZE);

    // Separate primes and non-primes into two lists
    Node* primes = nullptr;
    Node* non_primes = nullptr;
    int prime_count = 0, non_prime_count = 0;

    separate_primes(original, primes, non_primes, prime_count, non_prime_count);

    // Calculate the average of each list
    double prime_avg = calculate_average(primes);
    double non_prime_avg = calculate_average(non_primes);

    // Free all allocated memory
    free_list(original);
    free_list(primes);
    free_list(non_primes);

    return 0;
}
