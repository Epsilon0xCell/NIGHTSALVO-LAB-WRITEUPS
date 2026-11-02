// ret2win-overflow - a small buffer overflow lab by Gavin Blacklock
// win() is never called by the normal flow. The only way to reach it
// is to overwrite the saved return address in vuln().
#include <stdio.h>
#include <stdlib.h>

// gets() was removed from the C11 headers, so declare it by hand.
// The linker still provides it, and its lack of a length check is
// the whole point of this lab.
char *gets(char *s);

void win(void) {
    printf("You made it to win(). Flag: SALVO{r3t2w1n_0v3rfl0w}\n");
    fflush(stdout);
    exit(0);
}

void vuln(void) {
    char buffer[64];
    printf("Say something: ");
    fflush(stdout);
    // Deliberately unsafe for this lab. gets() has no length check.
    gets(buffer);
    printf("You said: %s\n", buffer);
}

int main(void) {
    vuln();
    printf("Nothing happened. Try again.\n");
    return 0;
}
