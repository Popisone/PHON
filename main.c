#include <stdio.h>
#include <stdint.h>
#include "phon_surrogate_model.h"

int main() {
    // Тестваме със същите ъгли като в Python теста
    float phases_rad[] = {0.0f, 1.57f, 3.14f, 4.71f};
    const char* labels[] = {"0° (Constructive)", "90° (Destructive)", "180° (Destructive)", "270° (Constructive)"};
    
    printf("--- Testing PHON Surrogate Model in C ---\n");
    for (int i = 0; i < 4; i++) {
        float features[1] = { phases_rad[i] };
        uint8_t result = predict(features);
        printf("%-20s | Phase: %.2f | Output: %u\n", labels[i], phases_rad[i], result);
    }
    
    return 0;
}