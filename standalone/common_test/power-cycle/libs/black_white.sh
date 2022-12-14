#!/bin/bash

function black_white_list
{
    local log_type=$1
    case $log_type in
        sel)
                black_list=(
                    "CATEER"
                    "unavailable"
                    "degraded"
                    "Deasserted"
                    "Critical "
                    "Uncorrectable ECC"
                    "Correctable ECC"
                    "Redundancy Lost"
                    "single-bit ECC"
                    "single bit error"
                    "going low"
                    "drop"
                    "warn"
                    "error"
                    "fail"
                    "lost"
                    "abnormal"
                    "fatal"
                    "ECC"
                    "unknown"
                    "CPU0_Prochot"
                    "CPU1_Prochot"
                    "CPU2_Prochot"
                    "CPU3_Prochot"
                    "CPU0_PROC_Hot"
                    "CPU1_PROC_Hot"
                    "CPU2_PROC_Hot"
                    "CPU3_PROC_Hot"
                    "Thermal Trip"
                    "NMI"
                    "Non-recoverable"
                    "going high"
                    "IERR"
                    "CATERR"
                    "flush_fail"
                    "corrected"
                    "Uncorrected"
                    "MCA"
                    "BMC_Boot_Up"
                    "abort"
                    "cancel"
                    "degrate"
                    "disconnect"
                    "expired" "Err"
                    "exception"
                    "Fault"
                    "halt"
                    "hot"
                    "insufficient"
                    "link down"
                    "linkdown"
                    "limit"
                    "miss"
                    "Mismatch"
                    "shutdown"
                    "shut down"
                    "shortage"
                    "unstable"
                    "unrecoverable"
                    "unreachable"
                    "warning"
                    "failed"
                    "failure"
                    "Critical"
                )
                white_list=(
                    "unknown|0xcb"
                    "fail|Connection activation failed: No suitable device found for this connection"
                    "reset|cleared"
                    "lost| AC"
                );;
        dmesg)
                black_list=(
                    "Blocked for more than x seconds"
                    "call trace"
                    "machine check events"
                    "resetting link"
                    "Unrecovered read error"
                    "Temperature above threshold"
                    "transmit timed out"
                    "out of memory"
                    "TSC unstable"
                    "error"
                    "machine check exception"
                    "hardware error"
                    "soft lockup"
                    "pcie error"
                    "media error"
                    "scsi hang"
                    "buffer i/o error"
                    "controller reset"
                    "io cancel"
                    "io error"
                    "being removed"
                    "CATEER"
                    "scrub error"
                    "Corrected"
                    "critical"
                    "degraded"
                    "dead device"
                    "Device offlined"
                    "device_unblocked"
                    "failure"
                    "fault"
                    "HDD block removing handle"
                    "IERR"
                    "lost"
                    "MCA"
                    "MCE Log"
                    "no readable"
                    "single-bit ECC"
                    "timeout"
                    "offline device"
                    "overcurrent"
                    "retry"
                    "uncorrect"
                    "Call Trace:"
                    "Ata error"
                    "I/O error"
                    "Medium Error"
                    "Blocked for more than"
                    "hard resetting link"
                    "FPDMA"
                    "Emask"
                    "task abort"
                    "correctable error"
                )
                white_list=(
                    "usb 1-1.2: clear tt 1"
                    "hub 1-1.2:1.0: hub_port_status failed (err = -71)"
                    "mei_me 0000:00:16.0: initialization failed"
                    "failed with error -22"
                    "failed to assign"
                    "drop_monitor: Initializing network drop monitor service"
                    "ignoring: Unit blk-availability.service failed to load: No such file or directory"
                    "ioapic:"
                    "Fast TSC calibration fail"
                    "ignoring: Unit blk-availability.service failed to"
                    "nfit ACPI0012:00: unknown table '7' parsing"
                    "drop_monitor: Initializing network drop monitor service"
                    "Driver 'tpm_tis' is already registered,"
                    "(ERST) support is"
                    "device not accepting address"
                    "can't set config #1,"
                    "string descriptor 0 read error:"
                    "Disable of device-initiated"
                    "module verification failed signature"
                    "hub_ext_port_status failed"
                    "BGRT failed to map image"
                    "failed to assign"
                    "failed to prefill DIMM database"
                    "kernel: Buffer I/O error on dev"
                    "failed to evaluate _DSM"
                    "hostbyte=DID_BAD_TARGET driverbyte=DRIVER_OK"
                    "augenrules: failure"
                    "hardware_error_device PNP0C33:00:"
                    "Timeout on hotplug command"
                    "tsc: Fast TSC calibration failed"
                    "couldn't mount because of unsupported optional feature"
                    "stat failed for file '/etc/netgroup'"
                    "(Sparql buffer) Error in task"
                    "dnssec-trigger-panel"
                    "fatal error: cannot setup ssl context"
                    "Starting Machine Check Exception Logging Daemon"
                    "Started Machine Check Exception Logging Daemon"
                    "01-dnssec-trigger-hook' exited with error"
                    "augenrules: lost"
                    "journal: Failed to load background"
                    "rc.local: error counts: 0"
                    "rc.local: Error response 0xc1 from Get PICMG Properities"
                    "Lost name on bus: org.gnome.SessionManager"
                    "GetManagedObjects() failed: org.freedesktop.DBus.Error.NoReply"
                    "Error releasing name org.gnome.SettingsDaemon"
                    "timeout set to"
                    "failed to INIT"
                );;
        messages)
                black_list=(
                    "hard resetting link"
                    "above  temperature"
                    "block & removing handle"
                    "error"
                    "machine check exception"
                    "machine check events"
                    "hardware error"
                    "soft lockup"
                    "pcie error"
                    "Media error"
                    "scsi hang"
                    "buffer i/o error"
                    "Unrecovered read error"
                    "out of memory"
                    "controller reset"
                    "io cancel"
                    "io error"
                    "being removed"
                    "CATEER"
                    "scrub error"
                    "Corrected"
                    "critical"
                    "degraded"
                    "dead device"
                    "Device offlined"
                    "device_unblocked"
                    "failure"
                    " fault"
                    "HDD block removing handle"
                    "IERR"
                    "lost"
                    "MCA"
                    "MCE Log"
                    "no readable"
                    "single-bit ECC"
                    "timeout"
                    "offline device"
                    "overcurrent"
                    "retry"
                    "uncorrect"
                    "Call Trace:"
                )
                white_list=(
                    "error opening USB device"
                    "Shutdown timeout set to"
                    "Correctable Errors collector"
                    "usb 1-1.6:"
                    "ast: module verification failed: signature and\/or required key missing - tainting kernel"
                    "Dependency failed for Network Manager Wait Online"
                    "srpd.service failed"
                    "Unit srpd.service entered failed state"
                    "network.service failed"
                    "Unit network.service entered failed state"
                    "(WW) warning, (EE) error, (NI) not implemented, (??) unknown"
                    "(EE) modeset(0): glamor initialization failed"
                    "rsyslogd-2307:"
                    "failed to assign"
                    "drop_monitor: Initializing network drop monitor service"
                    "Cannot add dependency job for unit multipathd.service, ignoring: Unit blk-availability.service failed to load: No such file or directory"
                    "\/usr\/lib\/systemd\/system-generators\/anaconda-generator failed with error code 1"
                    "Successfully dropped"
                    "rngd: read error"
                    "Family 6 Model 55 CPU: only decoding architectural errors"
                    "warning: 16 bytes ignored in each record"
                    "Sending warning via \/usr\/libexec\/smartmontools\/smartdnotify to root"
                    "\/etc\/NetworkManager\/dispatcher.d\/01-dnssec-trigger-hook"
                    "Couldn't find support for device at"
                    "gnome-session:"
                    "avahi-daemon:"
                    "error opening USB device 'descriptors' file"
                    "Unit run-media-root-ALICE.mount entered failed state"
                    "Job dev-sdb1.device\/start failed with result"
                    "No medium found"
                    "Unit mcelog.service entered failed state"
                    "mcelog.service failed"
                    "perf interrupt took too long"
                    "usb 1-1.2:"
                    "usb 1-1.2"
                    "dbus-daemon:"
                    "ioapic:"
                    "Fast TSC calibration fail"
                    "Successfully"
                    "rngd:"
                    "Sending warning"
                    "dbus[2371]:"
                    "dbus-org."
                    "nfit ACPI0012:00: unknown table '7' parsing"
                    "\/usr\/lib\/systemd\/system-generators\/anaconda-generator failed with error code"
                    "error opening USB device"
                    "drop_monitor: Initializing network drop monitor service"
                    "Script '\/etc\/NetworkManager\/dispatcher.d\/01-dnssec-trigger-hook' exited with error status 1"
                    "NetworkManager[1730]:"
                    "Driver 'tpm_tis' is already registered"
                    "(ERST) support is"
                    "device not accepting address"
                    "can't set config #1"
                    "string descriptor 0 read error"
                    "Disable of device-initiated"
                    "module verification failed signature"
                    "hub_ext_port_status failed"
                    "BGRT failed to map image"
                    "failed to assign"
                    "failed to prefill DIMM database"
                    "failed with error -22"
                    "kernel: Buffer I\/O error on dev"
                    "failed to evaluate _DSM"
                    "hostbyte=DID_BAD_TARGET driverbyte=DRIVER_OK"
                    "augenrules: failure"
                    "hardware_error_device PNP0C33:00:"
                    "Timeout on hotplug command"
                    "tsc: Fast TSC calibration failed"
                    "couldn't mount because of unsupported optional feature"
                    "stat failed for file '\/etc\/netgroup';"
                    "(Sparql buffer) Error in task"
                    "dnssec-trigger-panel"
                    "fatal error: cannot setup ssl context"
                    "Starting Machine Check Exception Logging Daemon"
                    "Started Machine Check Exception Logging Daemon"
                    "01-dnssec-trigger-hook' exited with error"
                    "augenrules: lost"
                    "journal: Failed to load background"
                    "rc.local: error counts: 0"
                    "rc.local: Error response 0xc1 from Get PICMG Properities"
                    "Lost name on bus: org.gnome.SessionManager"
                    "GetManagedObjects() failed: org.freedesktop.DBus.Error.NoReply"
                    "Error releasing name org.gnome.SettingsDaemon"
                    "timeout set to"
                    "failed to INIT"
                );;
        *)
            echo "log can not parse";;
    esac
}