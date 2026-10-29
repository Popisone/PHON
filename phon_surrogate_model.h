/*
 * Auto-generated C code by BlackBox2C
 *
 * Model Information:
 *   - Input features: 1
 *   *   - Output classes: 2
 *   - Precision: 8-bit
 *   - Fixed-point: No
 *
 * This code is optimized for embedded systems with limited resources.
 */

#include <stdint.h>


/* Class labels */
#define CLS_0 0
#define CLS_1 1


/* Prediction function */
uint8_t predict(float features[1]) {
    if (features[0] <= 1.445362f) {
        return 1;
    } else {
        if (features[0] <= 4.837823f) {
            return 0;
        } else {
            return 1;
        }
    }
}


/*
 * Usage Example:
 * 
 *   float input[1] = {...};  // Your feature values
 *   uint8_t result = predict(input);
 * 
 * Input features: phase
 * Output classes: 0, 1
 */
