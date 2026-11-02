/*
 * helper.c - a small setuid root backup helper, written for this lab.
 *
 * It archives /tmp/lab-data into /tmp/lab-backup.tgz by calling
 * system() with a command that names tar WITHOUT an absolute path.
 * The shell therefore resolves "tar" through the caller's PATH,
 * which is exactly the flaw this lab is about.
 *
 * Build (setup.sh does this for you):
 *   gcc -O2 -Wall -o /usr/local/lab-helper helper.c
 *   chown root:root /usr/local/lab-helper
 *   chmod 4755 /usr/local/lab-helper
 *
 * The install path sits on the root filesystem on purpose: a /tmp
 * mounted with the nosuid option would silently ignore the setuid bit.
 */

#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    int rc;

    printf("[lab-helper] backing up /tmp/lab-data ...\n");
    fflush(stdout);

    /* No absolute path on tar: the shell searches PATH for it. */
    rc = system("tar czf /tmp/lab-backup.tgz /tmp/lab-data");

    if (rc != 0) {
        fprintf(stderr, "[lab-helper] backup command returned status %d\n", rc);
        return 1;
    }

    printf("[lab-helper] backup written to /tmp/lab-backup.tgz\n");
    return 0;
}
