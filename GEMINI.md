# RaspNest

RaspNest is a project for controlling an RGB LED matrix connected to a Raspberry Pi using HTTP requests. It allows you to display various types of information on the matrix, such as time, weather, news, and stock prices.

## Features

*   **Modular Design:** The project is divided into a C++ core for low-level hardware control and a Python server for high-level application logic.
*   **Multiple Display Modes:** Supports various display modes, including a clock, weather forecast, news headlines, stock market data, and sports scores.
*   **Web-Based Control:** The display can be controlled through a web interface, allowing you to switch between different modes and customize the displayed information.
*   **Extensible:** The modular design makes it easy to add new display modes and data sources.

## Getting Started

### Prerequisites

*   Raspberry Pi with Raspbian OS installed
*   RGB LED matrix
*   C++ compiler and build tools
*   Python 3 and pip
*   Required Python libraries: `flask`, `requests`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/RaspNest.git
    ```
2.  **Build the C++ core:**
    ```bash
    cd RaspNest/c
    make
    ```
3.  **Install Python dependencies:**
    ```bash
    cd ../python_server
    pip install -r requirements.txt
    ```

### Usage

1.  **Start the Python server:**
    ```bash
    cd ../python_server
    python3 server.py
    ```
2.  **Open a web browser and navigate to `http://<your-raspberry-pi-ip-address>:5000`**
3.  **Use the web interface to control the display.**

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue if you find any bugs or have any suggestions for improvement.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
