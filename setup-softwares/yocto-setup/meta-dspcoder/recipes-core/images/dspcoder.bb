SUMMARY = "DSPCODER Minimal Image For Linux Device Driver Dev"
DESCRIPTION = "Small and fast-booting Linux image for driver experimentation"
LICENSE = "MIT"

inherit image

IMAGE_FEATURES += "debug-tweaks"

# Essential utilities for driver development
IMAGE_INSTALL = "\
    busybox \
    kernel-dev \
    kernel-modules \
    strace \
"
