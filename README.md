<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Linux Gaming Network Optimizer</title>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
    pre { background-color: #f4f4f4; padding: 10px; }
    code { background-color: #f4f4f4; padding: 2px 4px; }
  </style>
</head>
<body>
  <h1>Linux Gaming Network Optimizer</h1>
  <p>
    A Python-based GUI tool that optimizes network settings on Linux for gaming and real-time applications (e.g., FPS games like Counter-Strike). This application provides an easy-to-use interface (built with PyQt6) to adjust low-level network parameters for reduced latency and improved performance.
  </p>

  <h2>Features</h2>
  <ul>
    <li><strong>Cross-Distro Compatibility:</strong> Works on major Linux distributions (Ubuntu, Fedora, Arch, etc.) as long as the required dependencies are installed.</li>
    <li><strong>Network Interface Selection:</strong> Choose the network interface (excluding loopback) you want to optimize.</li>
    <li><strong>Latency Reduction:</strong> Disable offloading features (TSO, GSO, GRO) via <code>ethtool</code>.</li>
    <li><strong>Power Management:</strong> Option to disable power saving via <code>iw</code> or by automatically updating the NetworkManager configuration.</li>
    <li><strong>Buffer Sizes:</strong> Adjust network buffer sizes (0.5 MB to 4 MB) using a user-friendly slider with presets labeled as <em>Light</em>, <em>Balanced</em>, and <em>Heavy</em>.</li>
    <li><strong>TCP Congestion Control:</strong> Choose between congestion control algorithms (e.g., Cubic or BBR).</li>
    <li><strong>Reset Functionality:</strong> Revert all optimizations back to the system’s default settings with a single click.</li>
    <li><strong>Dependency Checker:</strong> Automatically checks for required dependencies (such as <code>ethtool</code>, <code>iw</code>, <code>sysctl</code>, and <code>pkexec</code>) and prompts the user to install them if they are missing.</li>
    <li><strong>Terminal Logging:</strong> Outputs debugging information to the terminal to confirm whether each setting was successfully applied.</li>
  </ul>

  <h2>Installation</h2>
  <h3>Requirements</h3>
  <ul>
    <li><strong>Python 3.x</strong></li>
    <li>
      <strong>PyQt6:</strong> Install via your package manager or using pip:
      <pre>pip install PyQt6</pre>
    </li>
    <li>
      <strong>ethtool:</strong>
      <pre>sudo apt install ethtool    # Debian/Ubuntu</pre>
    </li>
    <li>
      <strong>iw:</strong>
      <pre>sudo apt install iw         # Debian/Ubuntu</pre>
    </li>
    <li>
      <strong>pkexec:</strong> Typically provided by your distribution's PolicyKit package (e.g., <code>policykit-1</code> on Debian/Ubuntu).
    </li>
  </ul>

  <h3>Clone and Run</h3>
  <ol>
    <li>
      <strong>Clone the repository:</strong>
      <pre>git clone https://github.com/yourusername/linux-gaming-network-optimizer.git
cd linux-gaming-network-optimizer</pre>
    </li>
    <li>
      <strong>Make the script executable:</strong>
      <pre>chmod +x optimizer.py</pre>
    </li>
    <li>
      <strong>Run the program:</strong>
      <pre>./optimizer.py</pre>
    </li>
  </ol>
  <p>
    When launched, the program will check for any missing dependencies and prompt you to install them automatically.
  </p>

  <h2>Usage</h2>
  <ol>
    <li>
      <strong>Select Interface:</strong> Choose your network interface from the dropdown list (e.g., <code>eth0</code>, <code>wlan0</code>).
    </li>
    <li>
      <strong>Adjust Settings:</strong>
      <ul>
        <li><strong>Offloading Options:</strong> Toggle checkboxes to disable TSO, GSO, and GRO.</li>
        <li><strong>Power Saving:</strong> Check or uncheck the option to disable power saving. (If <code>iw</code> fails, the app will update the NetworkManager configuration.)</li>
        <li><strong>Buffer Sizes:</strong> Use the slider to set the desired buffer size in MB.</li>
        <li><strong>TCP Congestion Control:</strong> Select your preferred algorithm (Cubic or BBR).</li>
      </ul>
    </li>
    <li>
      <strong>Apply or Reset:</strong> Click <strong>Apply</strong> to enforce your changes immediately or <strong>Reset to Defaults</strong> to revert to the original system settings.
    </li>
    <li>
      <strong>Debugging:</strong> All changes and any error messages will be printed to the terminal, so run the program from a terminal window to see the detailed output.
    </li>
  </ol>

  <h2>Contributing</h2>
  <p>
    Contributions are welcome! If you have suggestions or bug reports, please open an issue or submit a pull request.
  </p>

  <h2>License</h2>
  <p>
    This project is licensed under the <a href="LICENSE">MIT License</a>.
  </p>

  <h2>Disclaimer</h2>
  <p>
    <strong>Warning:</strong> This tool makes changes to your system's network settings. Use it with caution and ensure you have proper backups and recovery methods in place. The author is not responsible for any issues or damages that may result from using this tool.
  </p>
</body>
</html>
