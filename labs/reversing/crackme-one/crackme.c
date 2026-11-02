// crackme-one - a small static analysis lab by Gavin Blacklock
// The password never appears in plain text. Each entered character is
// transformed and compared against the obfuscated bytes below.
#include <stdio.h>
#include <string.h>

static const unsigned char expected[] = {
    0x0c, 0x2a, 0x27, 0x29, 0x32, 0x14, 0x25, 0x29, 0x3c, 0x24, 0x69
};

int main(void) {
    char input[64];

    printf("Enter the password: ");
    fflush(stdout);

    if (fgets(input, sizeof(input), stdin) == NULL) {
        return 1;
    }
    input[strcspn(input, "\n")] = '\0';

    if (strlen(input) != sizeof(expected)) {
        printf("Access denied.\n");
        return 1;
    }

    for (size_t i = 0; i < sizeof(expected); i++) {
        unsigned char transformed = (unsigned char)((unsigned char)input[i] ^ 0x42 ^ (unsigned char)i);
        if (transformed != expected[i]) {
            printf("Access denied.\n");
            return 1;
        }
    }

    printf("Access granted. Flag: SALVO{st4t1c_4n4lys1s_w1ns}\n");
    return 0;
}
