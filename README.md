# OLX

## Overview

OLX is a Python software designed to fetch data from the OLX website, save it to a PostgreSQL database using SQLAlchemy, and export it to Telegram using Aiogram. The software utilizes aiohttp for asynchronous web scraping, anyio for high-level asynchronous operations, and asyncclick for a command-line interface.

## Features

- **Data Fetching:** The software allows you to scrape data from the OLX website using aiohttp, ensuring efficient and concurrent operations.

- **Database Integration:** The fetched data is stored in a PostgreSQL database, leveraging the power of SQLAlchemy to interact with the database. All necessary tables are created to save data obtained from the OLX API.

- **Telegram Export:** The software can export the fetched data to a Telegram channel or chat using Aiogram, providing a seamless way to share information.

- **Asynchronous Operations:** The software uses anyio to perform high-level asynchronous operations, enhancing efficiency and responsiveness.

- **Command-Line Interface:** The software offers a command-line interface powered by asyncclick, providing a user-friendly way to interact with the software.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/Jlgtri/olx.git
   cd olx
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup:**
   - Ensure that you have a PostgreSQL database available.

## Usage

### Command-Line Interface

OLX provides a command-line interface for easy interaction. Run the following command to see available commands:

```bash
python -m bin.main --help
```

## Contribution

Feel free to contribute to the project by opening issues, proposing new features, or submitting pull requests. Your contributions are highly appreciated!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
