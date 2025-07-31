SUMMARY = "DSPCODER Minimal Image for Linux Device Driver Development"
DESCRIPTION = "DSPCODER Linux image for working directly on linux device drivers, with Bash and kernel tools"
LICENSE = "MIT"

inherit core-image

# Switch to systemd init system
DISTRO_FEATURES:append = " systemd"
DISTRO_FEATURES:remove = "sysvinit x11 wayland"
VIRTUAL-RUNTIME_init_manager = "systemd"
VIRTUAL-RUNTIME_initscripts = ""
VIRTUAL-RUNTIME_login_manager = "systemd"

# Enable root login without password
IMAGE_FEATURES += "debug-tweaks"

# Install core tools for development
IMAGE_INSTALL = "\
    busybox \
    bash \
    kernel-modules \
    kernel-devsrc \
    kmod \
    udev \
    systemd \
    systemd-analyze \
    util-linux \
    coreutils \
"

# Add custom /etc/issue banner
ROOTFS_POSTPROCESS_COMMAND += "copy_issue_file;"
# Remove shutdown commands
ROOTFS_POSTPROCESS_COMMAND += "remove_shutdown_commands;"

# Function to copy your custom banner into the image
python copy_issue_file () {
    import shutil
    import os

    src = d.getVar('THISDIR')
    src_file = os.path.join(src, 'issue.txt')
    dest = os.path.join(d.getVar('IMAGE_ROOTFS'), 'etc', 'issue')

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(src_file):
        shutil.copyfile(src_file, dest)
    else:
        with open(dest, 'w') as f:
            f.write("DSPCoder Development Image\n")
}

# Function to remove shutdown commands
remove_shutdown_commands() {
    # Remove shutdown, poweroff, and halt commands
    rm -f ${IMAGE_ROOTFS}/sbin/shutdown
    rm -f ${IMAGE_ROOTFS}/sbin/poweroff
    rm -f ${IMAGE_ROOTFS}/sbin/halt
    
    # Also remove symbolic links in /usr/sbin if they exist
    rm -f ${IMAGE_ROOTFS}/usr/sbin/shutdown
    rm -f ${IMAGE_ROOTFS}/usr/sbin/poweroff
    rm -f ${IMAGE_ROOTFS}/usr/sbin/halt
    
}