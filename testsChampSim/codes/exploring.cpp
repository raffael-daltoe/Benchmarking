#include <iostream>
#include <cstdlib>
#include <ctime>

#define SIZE 10000000

volatile int sum = 0;

bool isPrimeRecursive(int num, int divisor = 2) {
    if (num <= 2) return (num == 2);
    if (num % divisor == 0) return false;
    if (divisor * divisor > num) return true;
    return isPrimeRecursive(num, divisor + 1);
}

void primeAction(int prime) {
    volatile int result = prime * 2; 
    (void)result; 
}

void nonPrimeAction(int number) {
    for (int i = 1; i <= 20; ++i) {
        if(isPrimeRecursive(sum)){
            primeAction(sum);
        }
        else{
            sum += number % i;
        }
    }
    (void)sum; 
}

void exploreBranchLocality() {
    for (int i = 0; i < SIZE; ++i) {
        int randomNumber = rand() % 1'000'000;
        if (isPrimeRecursive(randomNumber)) { 
            primeAction(randomNumber);
        }
        else{
            nonPrimeAction(randomNumber);
        }
    }
}

int main() {
    srand(static_cast<unsigned>(time(0)));
    exploreBranchLocality();
    return 0;
}
