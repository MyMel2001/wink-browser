# 😉 Wink Browser

A modern, privacy-focused web browser built in Python.

## Features

- **Privacy First**: Built-in ad and tracker blocking
- **Modern UI**: Clean, intuitive interface built with Python and Tkinter
- **Customizable**: Extensive settings to tailor your browsing experience
- **Lightweight**: Efficient resource usage compared to mainstream browsers
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Extension Support**: Support for securely sandboxed browser extensions
- **Brand New Browser Engine**: Not any existing browser engine of any kind.
- **Freedom from big tech**: No influence from big tech.

## Components

- **HTML Parser**: Efficient HTML parsing using BeautifulSoup and html5lib
- **CSS Parser**: CSS parsing and styling with cssutils (WIP)
- **JavaScript Engine**: JavaScript execution via dukpy (embedded JavaScript interpreter)
- **Network Manager**: Handles HTTP requests, cookies, and caching
- **Ad Blocker**: Blocks ads and trackers using filter lists
- **Download Manager**: Manages file downloads with pause/resume support
- **History Manager**: Tracks and manages browsing history
- **Bookmark Manager**: Organizes and stores bookmarks
- **Extensions System**: Secure, sandboxed browser extensions
- **Secure, sanitized JavaScript**: Implements rigorous filtering and sandboxing to prevent malicious scripts from executing while maintaining some level of compatibility with standard web functionality

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/sneed-group/wink-browser.git
   cd wink-browser
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the browser:
   ```
   python main.py
   ```

## Usage

Wink Browser supports several command-line options:

- **Regular Mode**: `python main.py [url]`
- **Text-Only Mode**: `python main.py --text-only [url]` (Disables everything except plain text, including links and images, for faster, lighter browsing)
- **Private Mode**: `python main.py --private [url]` (No history or cookies saved)
- **Debug Mode**: `python main.py --debug [url]` (Shows detailed debug information)

You can combine these options. For example, to run in both private and text-only mode:
```
python main.py --private --text-only https://example.com
```

### Known Issues and Workarounds

- **SSL Certificate Errors**: If you encounter SSL certificate verification errors, the browser will automatically retry without verification as a fallback. This is not recommended for security-sensitive browsing.
  
- **JavaScript Engine Issues**: The JavaScript engine may occasionally encounter event loop errors. If this happens, try using text-only mode (`--text-only` flag) which disables JavaScript execution. (Note that this also disables all links and images, so beware.)

## Configuration

Wink Browser stores its configuration in `~/.wink_browser/config.json`. This includes:

- General settings (homepage, search engine, etc.)
- Privacy settings (cookie policy, tracking protection)
- Ad blocker settings (filter lists, custom rules)
- Advanced settings (JavaScript, cache size, etc.)
- Extension settings and permissions

## Extensions

Wink Browser supports extensions that can enhance your browsing experience:

### Extension Structure

Extensions are stored in `~/.wink_browser/extensions/` with each extension in its own folder. An extension consists of:

- `extprops.csv`: Defines extension metadata and event handlers
- JavaScript files that handle different browser events

Example `extprops.csv`:
```csv
Key,Value
@name,My Extension
@version,1.0.0
@description,An example extension
@enabled,true

Script,Events
main.js,page_load,dom_ready
link_handler.js,link_click
```

### Extension Security

Extensions run in an even more secure sandbox with:

- JavaScript code filtering to block potentially harmful patterns
- Limited API access based on permissions
- Event-based architecture to minimize resource usage
- Isolation from the main browser context

### Creating Extensions

To create example extensions, run:
```
python -m browser_engine.extensions.setup_extensions
```

## Comparing and contrasting Wink to TempleOS (for the lols)

***TempleOS and wink have a few similarities...***

- They were both created/founded by a person diagnosed with paranoia
- They were both created/founded by that one person, and the power of God. (If he exists.)
- Both are spawns of some sort of "divine intervention..." (I was told in my dreams the specifications, Terry was "told by god" the specifications "god wanted")

***...Although, my project and Terry's project have one major difference.***

Mine is assisted by AI, his was made by himself (and God) alone. (Terry Davis would probably hate AI, if not then he would likely hate how I, the creator (Sparksammy/NodeMixaholic), use it.)

## Development

### Project Structure

```
wink-browser/
├── browser_engine/          # Core browser engine
│   ├── parser/              # HTML, CSS, and JS parsers
│   ├── privacy/             # Privacy features (ad blocker, etc.)
│   ├── media/               # Media handling (images, video, audio)
│   ├── extensions/          # Extension system
│   ├── ui/                  # User interface components
│   └── utils/               # Utility modules
├── main.py                  # Entry point
└── requirements.txt         # Dependencies
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## Describing how we use checkpoints in commit names.

- Major/big/giant checkpoint - Used after quite a few major, now stable changes were made.
- Checkpoint - used after some small-medium sized changes were made that are now stable.
- Small/Tiny checkpoint - Used after several tiny changes known to be stable were made.

## License

This project is licensed under the Sammy Public License - see the LICENSE file for details.

## Acknowledgments

- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- [cssutils](https://pypi.org/project/cssutils/) for CSS parsing
- [dukpy](https://github.com/amol-/dukpy) for JavaScript execution
- [Requests](https://requests.readthedocs.io/) for HTTP handling
- [Tkinter](https://docs.python.org/3/library/tkinter.html) for the UI 
- [Python](https://python.org) for the programming language 
