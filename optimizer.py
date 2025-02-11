#!/usr/bin/env python3
"""
Linux Network Optimizer for Gaming and Real-Time Applications

This Python program uses PyQt6 to provide a simple graphical interface that allows users
to optimize network settings (e.g., disable TCP offloading, adjust buffer sizes, select
TCP congestion control) for improved gaming performance on Linux.

Key Features:
  - Cross-distro compatibility (Ubuntu, Fedora, Arch, etc.)
  - Network interface selection (excluding loopback)
  - Latency reduction (disable TSO, GSO, GRO via ethtool)
  - Option to disable power saving on the selected interface (via iw or by updating the
    NetworkManager configuration)
  - User-friendly buffer controls (slider labeled in MB with presets: Light, Balanced, Heavy)
  - TCP congestion control selection (e.g., cubic, bbr)
  - "Reset to Defaults" functionality (restores original settings detected on startup)
  - Immediate effect: changes are applied immediately via sysctl/ethtool/iw
  - Minimal dependencies and clear error handling
  - Uses pkexec to ensure all system changes run with root privileges (only one authentication prompt)

Installation instructions:
  - Install PyQt6: e.g., on Debian/Ubuntu: sudo apt install python3-pyqt6
  - Install ethtool and iw: e.g., sudo apt install ethtool iw
  - Run this script normally (it will automatically re-launch itself via pkexec if needed)

Author: [Your Name]
Date: [Date]
"""

import os
import sys
import subprocess
import shutil  # For checking if required commands are available
from PyQt6 import QtWidgets, QtCore

# --- New Helper Functions for Dependency Checking and Installation ---

def ask_install_missing(missing):
    """
    Ask the user (via a GUI message box if possible or via terminal) if they want to install the missing dependencies.
    Returns True if the user agrees, False otherwise.
    """
    msg = ("The following dependencies are missing:\n" +
           ", ".join(missing) +
           "\n\nDo you want to install them automatically?")
    # Try to use a Qt message box if a QApplication exists; otherwise, use input().
    if QtWidgets.QApplication.instance() is None:
        try:
            app = QtWidgets.QApplication(sys.argv)
            created_app = True
        except Exception:
            created_app = False
    else:
        created_app = False

    try:
        reply = QtWidgets.QMessageBox.question(None, "Missing Dependencies", msg,
                                               QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        answer = (reply == QtWidgets.QMessageBox.StandardButton.Yes)
    except Exception:
        # Fallback to terminal prompt.
        answer = input(msg + " [Y/n]: ").lower() in ["y", "yes", ""]
    if created_app:
        app.quit()
    return answer

def detect_package_manager():
    """
    Try to detect a known package manager.
    Returns one of "apt-get", "dnf", "yum", or "pacman", or None if not found.
    """
    for mgr in ["apt-get", "dnf", "yum", "pacman"]:
        if shutil.which(mgr) is not None:
            return mgr
    return None

def install_dependencies(missing):
    """
    Attempt to install the missing dependencies.
    Uses the detected package manager and maps each dependency to a package name.
    """
    pkg_mgr = detect_package_manager()
    if pkg_mgr is None:
        sys.stderr.write("No supported package manager found. Please install the missing packages manually.\n")
        return False

    # Map the required command to the package name for each package manager.
    package_map = {
        "ethtool": {
            "apt-get": "ethtool",
            "dnf": "ethtool",
            "yum": "ethtool",
            "pacman": "ethtool",
        },
        "iw": {
            "apt-get": "iw",
            "dnf": "iw",
            "yum": "iw",
            "pacman": "iw",
        },
        "sysctl": {
            "apt-get": "procps",
            "dnf": "procps-ng",
            "yum": "procps-ng",
            "pacman": "procps-ng",
        },
        "pkexec": {
            "apt-get": "policykit-1",
            "dnf": "polkit",
            "yum": "polkit",
            "pacman": "polkit",
        }
    }
    # Build list of package names.
    packages = []
    for dep in missing:
        pkg = package_map.get(dep, {}).get(pkg_mgr)
        if pkg:
            packages.append(pkg)
        else:
            packages.append(dep)  # Fallback to the command name

    install_cmd = []
    if pkg_mgr == "apt-get":
        install_cmd = ["apt-get", "update", "&&", "apt-get", "install", "-y"] + packages
        # Note: Running "apt-get update" inline is simplistic; you may wish to split it.
        install_cmd = " ".join(install_cmd)
    elif pkg_mgr == "dnf":
        install_cmd = ["dnf", "install", "-y"] + packages
    elif pkg_mgr == "yum":
        install_cmd = ["yum", "install", "-y"] + packages
    elif pkg_mgr == "pacman":
        install_cmd = ["pacman", "-S", "--noconfirm"] + packages

    sys.stdout.write("Attempting to install missing dependencies using {}...\n".format(pkg_mgr))
    try:
        if pkg_mgr == "apt-get":
            # For apt-get, run update then install.
            subprocess.check_call(["apt-get", "update"])
            subprocess.check_call(["apt-get", "install", "-y"] + packages)
        else:
            subprocess.check_call(install_cmd)
        sys.stdout.write("Installation successful.\n")
        return True
    except subprocess.CalledProcessError as e:
        sys.stderr.write("Failed to install dependencies: {}\n".format(e))
        return False

def check_dependencies():
    """
    Check for required external dependencies.
    If any are missing, ask the user if they want to install them.
    Returns True if all are present (or successfully installed), otherwise False.
    """
    required_commands = ["ethtool", "iw", "sysctl", "pkexec"]
    missing = [cmd for cmd in required_commands if shutil.which(cmd) is None]
    if missing:
        sys.stderr.write("Missing dependencies: " + ", ".join(missing) + "\n")
        if ask_install_missing(missing):
            if not install_dependencies(missing):
                sys.stderr.write("Installation of dependencies failed. Exiting.\n")
                return False
            # Re-check dependencies
            missing = [cmd for cmd in required_commands if shutil.which(cmd) is None]
            if missing:
                sys.stderr.write("The following dependencies are still missing after installation: " + ", ".join(missing) + "\n")
                return False
            return True
        else:
            return False
    return True

# --- End Dependency-Check Functions ---

class NetworkOptimizer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux Network Optimizer for Gaming")
        self.resize(600, 400)

        # Dictionaries to store default settings (to allow reset)
        self.global_defaults = {}      # For sysctl/global settings
        self.interface_defaults = {}   # Per-interface defaults (offloading, power save)
        self.current_interface = None
        self.available_interfaces = []

        self.initUI()
        self.load_interfaces()

        if self.available_interfaces:
            # Set the first (non-loopback) interface as current
            self.interfaceComboBox.setCurrentIndex(0)
            self.load_interface_settings(self.available_interfaces[0])
        self.load_global_defaults()

    def initUI(self):
        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        layout = QtWidgets.QVBoxLayout(centralWidget)

        # ===== Network Interface Selection =====
        interfaceLayout = QtWidgets.QHBoxLayout()
        interfaceLabel = QtWidgets.QLabel("Select Network Interface:")
        self.interfaceComboBox = QtWidgets.QComboBox()
        self.interfaceComboBox.setToolTip("Choose the network interface to optimize (e.g., eth0, wlan0). Loopback is not listed.")
        self.interfaceComboBox.currentTextChanged.connect(self.on_interface_change)
        interfaceLayout.addWidget(interfaceLabel)
        interfaceLayout.addWidget(self.interfaceComboBox)
        layout.addLayout(interfaceLayout)

        # ===== Offloading Options =====
        offloadingGroupBox = QtWidgets.QGroupBox("Offloading Options (Disable for lower latency)")
        offloadingLayout = QtWidgets.QVBoxLayout()
        self.tsoCheckBox = QtWidgets.QCheckBox("Disable TSO")
        self.tsoCheckBox.setToolTip("Disable TCP Segmentation Offload (TSO). This may reduce latency in some cases.")
        self.gsoCheckBox = QtWidgets.QCheckBox("Disable GSO")
        self.gsoCheckBox.setToolTip("Disable Generic Segmentation Offload (GSO). This may reduce latency in some cases.")
        self.groCheckBox = QtWidgets.QCheckBox("Disable GRO")
        self.groCheckBox.setToolTip("Disable Generic Receive Offload (GRO). This may reduce latency in some cases.")
        offloadingLayout.addWidget(self.tsoCheckBox)
        offloadingLayout.addWidget(self.gsoCheckBox)
        offloadingLayout.addWidget(self.groCheckBox)
        offloadingGroupBox.setLayout(offloadingLayout)
        layout.addWidget(offloadingGroupBox)

        # ===== Power Management =====
        self.powerSaveCheckBox = QtWidgets.QCheckBox("Disable Power Saving (for better responsiveness)")
        self.powerSaveCheckBox.setToolTip("Disable power saving mode on the interface. If your hardware does not support this via 'iw', the NetworkManager config will be updated to disable WiFi power saving.")
        layout.addWidget(self.powerSaveCheckBox)

        # ===== Buffer Sizes =====
        bufferGroupBox = QtWidgets.QGroupBox("Buffer Sizes (Adjust based on usage)")
        bufferLayout = QtWidgets.QVBoxLayout()
        sliderLayout = QtWidgets.QHBoxLayout()
        sliderLabel = QtWidgets.QLabel("Buffer Size:")
        self.bufferSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        # Slider values: 1 corresponds to 0.5MB, up to 8 = 4MB (step size 0.5MB)
        self.bufferSlider.setMinimum(1)
        self.bufferSlider.setMaximum(8)
        self.bufferSlider.setValue(4)  # Default to "Balanced" (i.e. 2.0 MB)
        self.bufferSlider.setTickInterval(1)
        self.bufferSlider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.bufferSlider.setToolTip("Adjust network buffer sizes for real-time performance. Range: 0.5 MB (Light) to 4 MB (Heavy).")
        self.bufferSlider.valueChanged.connect(self.update_buffer_label)
        self.bufferLabel = QtWidgets.QLabel("2.0 MB (Balanced)")
        sliderLayout.addWidget(sliderLabel)
        sliderLayout.addWidget(self.bufferSlider)
        sliderLayout.addWidget(self.bufferLabel)
        bufferLayout.addLayout(sliderLayout)
        bufferGroupBox.setLayout(bufferLayout)
        layout.addWidget(bufferGroupBox)

        # ===== TCP Congestion Control =====
        tcpLayout = QtWidgets.QHBoxLayout()
        tcpLabel = QtWidgets.QLabel("TCP Congestion Control:")
        self.tcpComboBox = QtWidgets.QComboBox()
        # Add common algorithms; note: BBR requires kernel support.
        self.tcpComboBox.addItems(["cubic", "bbr"])
        self.tcpComboBox.setToolTip("Select the TCP congestion control algorithm. BBR and Cubic are supported (BBR requires kernel support).")
        tcpLayout.addWidget(tcpLabel)
        tcpLayout.addWidget(self.tcpComboBox)
        layout.addLayout(tcpLayout)

        # ===== Action Buttons =====
        buttonLayout = QtWidgets.QHBoxLayout()
        self.applyButton = QtWidgets.QPushButton("Apply")
        self.applyButton.setToolTip("Apply the selected network optimizations immediately.")
        self.applyButton.clicked.connect(self.apply_settings)
        self.resetButton = QtWidgets.QPushButton("Reset to Defaults")
        self.resetButton.setToolTip("Revert all settings to the system defaults detected on startup.")
        self.resetButton.clicked.connect(self.reset_to_defaults)
        buttonLayout.addWidget(self.applyButton)
        buttonLayout.addWidget(self.resetButton)
        layout.addLayout(buttonLayout)

    def load_interfaces(self):
        """Load network interfaces from /sys/class/net (excluding loopback)."""
        try:
            interfaces = os.listdir("/sys/class/net")
            # Exclude the loopback interface
            self.available_interfaces = [iface for iface in interfaces if iface != "lo"]
            self.interfaceComboBox.addItems(self.available_interfaces)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error",
                f"Failed to list network interfaces:\n{str(e)}")

    def load_interface_settings(self, interface):
        """
        For the given network interface, detect the current offloading and power
        saving settings and update the UI accordingly.
        """
        self.current_interface = interface

        # If we have not stored the defaults for this interface yet, detect them.
        if interface not in self.interface_defaults:
            self.interface_defaults[interface] = {}

            # --- Detect offloading settings via ethtool ---
            try:
                output = subprocess.check_output(["ethtool", "-k", interface], text=True)
                for line in output.splitlines():
                    line = line.strip()
                    if ("tcp-segmentation-offload:" in line) or ("tso:" in line):
                        value = line.split(":")[-1].strip()
                        self.interface_defaults[interface]['tso'] = (value.lower() == "on")
                    elif ("generic-segmentation-offload:" in line) or ("gso:" in line):
                        value = line.split(":")[-1].strip()
                        self.interface_defaults[interface]['gso'] = (value.lower() == "on")
                    elif ("generic-receive-offload:" in line) or ("gro:" in line):
                        value = line.split(":")[-1].strip()
                        self.interface_defaults[interface]['gro'] = (value.lower() == "on")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Warning",
                    f"Failed to get offloading settings for {interface}:\n{str(e)}")
                # Assume defaults “on” if detection fails.
                self.interface_defaults[interface]['tso'] = True
                self.interface_defaults[interface]['gso'] = True
                self.interface_defaults[interface]['gro'] = True

            # --- Detect power saving settings via iw (if applicable) ---
            try:
                # This command may only work for wireless interfaces.
                output = subprocess.check_output(["iw", "dev", interface, "get", "power_save"], text=True).strip()
                # Expected output might be like "Power save: off" or "Power save: on"
                if "off" in output.lower():
                    self.interface_defaults[interface]['power_save'] = False
                else:
                    self.interface_defaults[interface]['power_save'] = True
            except Exception:
                # If the command fails (e.g. for non-wireless interfaces), mark as not applicable.
                self.interface_defaults[interface]['power_save'] = None

        # --- Update UI based on detected settings ---
        defaults = self.interface_defaults[interface]
        # For offloading, the checkboxes mean "Disable" – so if offloading is currently enabled (True),
        # then the box should be unchecked; if offloading is disabled (False), then check the box.
        self.tsoCheckBox.setChecked(not defaults.get('tso', True))
        self.gsoCheckBox.setChecked(not defaults.get('gso', True))
        self.groCheckBox.setChecked(not defaults.get('gro', True))

        # For power saving: if not applicable, disable the checkbox.
        if defaults.get('power_save') is not None:
            self.powerSaveCheckBox.setEnabled(True)
            self.powerSaveCheckBox.setChecked(not defaults.get('power_save'))
        else:
            self.powerSaveCheckBox.setEnabled(False)
            self.powerSaveCheckBox.setChecked(False)

        # --- Global settings (buffer sizes and TCP congestion control) ---
        try:
            rmem = subprocess.check_output(["sysctl", "-n", "net.core.rmem_max"], text=True).strip()
            # Convert bytes to MB (using 1 MB = 1048576 bytes)
            buffer_mb = int(rmem) / 1048576
            # Calculate the slider value (each step represents 0.5 MB)
            slider_value = max(1, min(8, int(round(buffer_mb / 0.5))))
            self.bufferSlider.setValue(slider_value)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Warning",
                f"Failed to get buffer sizes:\n{str(e)}")

        try:
            tcp_cc = subprocess.check_output(["sysctl", "-n", "net.ipv4.tcp_congestion_control"], text=True).strip()
            index = self.tcpComboBox.findText(tcp_cc)
            if index != -1:
                self.tcpComboBox.setCurrentIndex(index)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Warning",
                f"Failed to get TCP congestion control:\n{str(e)}")

    def load_global_defaults(self):
        """Store global settings (buffer sizes and TCP congestion control) for later reset."""
        if not self.global_defaults:
            try:
                rmem = subprocess.check_output(["sysctl", "-n", "net.core.rmem_max"], text=True).strip()
                wmem = subprocess.check_output(["sysctl", "-n", "net.core.wmem_max"], text=True).strip()
                tcp_cc = subprocess.check_output(["sysctl", "-n", "net.ipv4.tcp_congestion_control"], text=True).strip()
                self.global_defaults['net.core.rmem_max'] = rmem
                self.global_defaults['net.core.wmem_max'] = wmem
                self.global_defaults['net.ipv4.tcp_congestion_control'] = tcp_cc
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Warning",
                    f"Failed to load global defaults:\n{str(e)}")

    def on_interface_change(self, interface):
        """When the user selects a different interface, load its current settings."""
        self.load_interface_settings(interface)

    def update_buffer_label(self, value):
        """
        Update the label next to the slider. The slider value (1-8) is interpreted as a multiple
        of 0.5 MB. Also, provide a preset label:
            - Light:   0.5-1 MB
            - Balanced: ~1-2.5 MB
            - Heavy:   >2.5 MB
        """
        buffer_mb = value * 0.5
        if value <= 2:
            preset = "Light"
        elif value <= 5:
            preset = "Balanced"
        else:
            preset = "Heavy"
        self.bufferLabel.setText(f"{buffer_mb:.1f} MB ({preset})")

    def apply_settings(self):
        """
        Apply the current settings as selected in the GUI:
          - Adjust offloading (TSO, GSO, GRO) per the checkboxes.
          - Toggle power saving via iw or, if that fails for disabling, via NetworkManager config.
          - Adjust buffer sizes via sysctl.
          - Change TCP congestion control via sysctl.
        Also prints the outcome of each change to the terminal.
        """
        interface = self.current_interface
        if not interface:
            QtWidgets.QMessageBox.warning(self, "Error", "No network interface selected.")
            return

        error_messages = []

        # --- Offloading Settings ---
        try:
            if self.tsoCheckBox.isChecked():
                subprocess.check_call(["ethtool", "-K", interface, "tso", "off"])
                print(f"Successfully disabled TSO on {interface}.")
            else:
                subprocess.check_call(["ethtool", "-K", interface, "tso", "on"])
                print(f"Successfully enabled TSO on {interface}.")
        except Exception as e:
            error_messages.append(f"Failed to set TSO for {interface}: {str(e)}")
        try:
            if self.gsoCheckBox.isChecked():
                subprocess.check_call(["ethtool", "-K", interface, "gso", "off"])
                print(f"Successfully disabled GSO on {interface}.")
            else:
                subprocess.check_call(["ethtool", "-K", interface, "gso", "on"])
                print(f"Successfully enabled GSO on {interface}.")
        except Exception as e:
            error_messages.append(f"Failed to set GSO for {interface}: {str(e)}")
        try:
            if self.groCheckBox.isChecked():
                subprocess.check_call(["ethtool", "-K", interface, "gro", "off"])
                print(f"Successfully disabled GRO on {interface}.")
            else:
                subprocess.check_call(["ethtool", "-K", interface, "gro", "on"])
                print(f"Successfully enabled GRO on {interface}.")
        except Exception as e:
            error_messages.append(f"Failed to set GRO for {interface}: {str(e)}")

        # --- Power Saving Setting ---
        if self.powerSaveCheckBox.isEnabled():
            try:
                if self.powerSaveCheckBox.isChecked():
                    # Attempt to disable power saving via iw
                    subprocess.check_call(["iw", "dev", interface, "set", "power_save", "off"])
                    print(f"Successfully disabled power saving via iw on {interface}.")
                else:
                    subprocess.check_call(["iw", "dev", interface, "set", "power_save", "on"])
                    print(f"Successfully enabled power saving via iw on {interface}.")
            except Exception as e:
                # Fallback: if user is trying to disable power saving, update the NM config file.
                if self.powerSaveCheckBox.isChecked():
                    try:
                        file_path = "/etc/NetworkManager/conf.d/default-wifi-powersave-on.conf"
                        config_str = "[connection]\nwifi.powersave = 2\n"
                        with open(file_path, "w") as f:
                            f.write(config_str)
                        print(f"Successfully disabled power saving via NetworkManager config on {interface}.")
                    except Exception as e2:
                        error_messages.append(f"Failed to disable power saving for {interface} (fallback via NM config also failed): {str(e2)}")
                else:
                    error_messages.append(f"Failed to set power saving for {interface}: {str(e)}")

        # --- Buffer Sizes ---
        buffer_value = int(self.bufferSlider.value() * 0.5 * 1048576)  # in bytes
        try:
            subprocess.check_call(["sysctl", "-w", f"net.core.rmem_max={buffer_value}"])
            subprocess.check_call(["sysctl", "-w", f"net.core.wmem_max={buffer_value}"])
            print(f"Successfully set buffer sizes to {self.bufferSlider.value() * 0.5} MB on {interface}.")
        except Exception as e:
            error_messages.append(f"Failed to set buffer sizes: {str(e)}")

        # --- TCP Congestion Control ---
        tcp_cc = self.tcpComboBox.currentText()
        try:
            subprocess.check_call(["sysctl", "-w", f"net.ipv4.tcp_congestion_control={tcp_cc}"])
            print(f"Successfully set TCP congestion control to {tcp_cc} on {interface}.")
        except Exception as e:
            error_messages.append(f"Failed to set TCP congestion control: {str(e)}")

        # --- Final Feedback ---
        if error_messages:
            QtWidgets.QMessageBox.warning(self, "Errors Occurred", "\n".join(error_messages))
            print("Errors occurred during applying settings:")
            for msg in error_messages:
                print(msg)
        else:
            QtWidgets.QMessageBox.information(self, "Success", "Settings applied successfully.")
            print("All settings applied successfully.")

    def reset_to_defaults(self):
        """
        Reset all settings to their original (default) values as detected on startup.
        This includes per-interface offloading/power settings and global sysctl parameters.
        Also prints the outcome of each reset command to the terminal.
        """
        interface = self.current_interface
        if not interface:
            QtWidgets.QMessageBox.warning(self, "Error", "No network interface selected.")
            return

        error_messages = []
        defaults = self.interface_defaults.get(interface, {})

        # --- Reset Offloading Settings ---
        try:
            tso_default = "on" if defaults.get('tso', True) else "off"
            subprocess.check_call(["ethtool", "-K", interface, "tso", tso_default])
            print(f"Successfully reset TSO to default ({tso_default}) on {interface}.")
        except Exception as e:
            error_messages.append(f"Failed to reset TSO for {interface}: {str(e)}")
        try:
            gso_default = "on" if defaults.get('gso', True) else "off"
            subprocess.check_call(["ethtool", "-K", interface, "gso", gso_default])
            print(f"Successfully reset GSO to default ({gso_default}) on {interface}.")
        except Exception as e:
            error_messages.append(f"Failed to reset GSO for {interface}: {str(e)}")
        try:
            gro_default = "on" if defaults.get('gro', True) else "off"
            subprocess.check_call(["ethtool", "-K", interface, "gro", gro_default])
            print(f"Successfully reset GRO to default ({gro_default}) on {interface}.")
        except Exception as e:
            error_messages.append(f"Failed to reset GRO for {interface}: {str(e)}")

        # --- Reset Power Saving (if applicable) ---
        if defaults.get('power_save') is not None:
            try:
                ps_default = "on" if defaults.get('power_save') else "off"
                subprocess.check_call(["iw", "dev", interface, "set", "power_save", ps_default])
                print(f"Successfully reset power saving to default ({ps_default}) on {interface}.")
            except Exception as e:
                error_messages.append(f"Failed to reset power saving for {interface}: {str(e)}")

        # --- Reset Global Settings ---
        try:
            subprocess.check_call(["sysctl", "-w", f"net.core.rmem_max={self.global_defaults.get('net.core.rmem_max')}"])
            subprocess.check_call(["sysctl", "-w", f"net.core.wmem_max={self.global_defaults.get('net.core.wmem_max')}"])
            print("Successfully reset buffer sizes to defaults.")
        except Exception as e:
            error_messages.append(f"Failed to reset buffer sizes: {str(e)}")
        try:
            subprocess.check_call(["sysctl", "-w", f"net.ipv4.tcp_congestion_control={self.global_defaults.get('net.ipv4.tcp_congestion_control')}"])
            print("Successfully reset TCP congestion control to default.")
        except Exception as e:
            error_messages.append(f"Failed to reset TCP congestion control: {str(e)}")

        if error_messages:
            QtWidgets.QMessageBox.warning(self, "Errors Occurred", "\n".join(error_messages))
            print("Errors occurred during resetting to defaults:")
            for msg in error_messages:
                print(msg)
        else:
            QtWidgets.QMessageBox.information(self, "Success", "Settings reset to defaults successfully.")
            print("All settings reset to defaults successfully.")
            # Reload the settings to update the UI
            self.load_interface_settings(interface)

def main():
    """
    Main entry point:
      - Checks for required dependencies.
      - Checks if running as root; if not, re-launches using pkexec with DISPLAY and XAUTHORITY set.
      - Then starts the PyQt6 application.
    """
    if not check_dependencies():
        sys.exit(1)

    if os.geteuid() != 0:
        env = os.environ.copy()
        # Use the absolute path of the script.
        script_path = os.path.realpath(__file__)
        cmd = ["pkexec", "env", f"DISPLAY={env.get('DISPLAY', '')}", f"XAUTHORITY={env.get('XAUTHORITY', '')}", sys.executable, script_path] + sys.argv[1:]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            print("Failed to gain root privileges via pkexec.")
        sys.exit(0)

    app = QtWidgets.QApplication(sys.argv)
    window = NetworkOptimizer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

