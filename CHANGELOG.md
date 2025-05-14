# Changelog

## [0.6.1] - (CLI Stability & Python 3.14 Support)

#### Added

- Support for Python 3.14 development versions in CI test matrix
- Python 3.14 classifier added to `pyproject.toml` for future compatibility

#### Changed

- CLI demo command updated to use `uv run` for operational consistency
- Demo GIF and link for CLI updated in documentation with a new version

#### Fixed

- Critical CLI functionality restored by updating `click` dependency to version `8.1.8`
- Formatting of OS matrix in CI workflow configuration corrected

#### Dependencies

- `click` (transitive via `typer`) updated to version `8.1.8`

## [0.6.0] - (New YouTube Support, `uv` Migration & Enhancements)

#### Added

- New YouTube download support leveraging [StreamSnapper](https://github.com/henrique-coder/streamsnapper) for optimal stream selection
- Full project migration to `uv` for dependency and environment management (`uv.lock`)
- Optional installation extra: `[cli]` for CLI support
- New `.python-version` file specifying Python 3.13 for consistent development

#### Changed

- Build system transitioned from Poetry-core to Hatchling for package building
- Project source code fully consolidated into `src/turbodl` directory structure
- Makefile commands streamlined and help text improved for better usability
- README updated with YouTube feature details and improved installation instructions
- Internal comment terminology standardized to "Local modules" for code clarity
- `streamsnapper` dependency is now a core requirement for all installations
- `typer` dependency for CLI made optional, managed via the new `[cli]` extra

#### Fixed

- Internal module import paths standardized to `src.turbodl` for consistency
- Error handling improved for missing optional CLI dependencies at runtime
- Connection calculation logic in `calculate_max_connections` optimized
- Unused `expected_hash` parameter removed from `download_single_file` method
- Default Python interpreter in Makefile set to `python` for wider compatibility
- File hashes for `urllib3` dependency updated to ensure integrity
- Linting and formatting rules in `ruff.toml` updated and refined

#### Dependencies

- `ruff` updated to version `^0.11.9`
- `typer` updated to version `^0.15.3` (now optional via `[cli]` extra)
- `urllib3` (transitive) updated to version `2.4.0` via direct resolution

## [0.5.2] - (Enhanced HTTP Features & Connection Management)

#### Changed

- Streamlined HTTP client initialization and enhanced file info fetching logic
- Updated RemoteFileInfo size type to allow "unknown" and improved URL validation
- Simplified argument annotations for better code clarity
- Enhanced documentation for clarity and consistency

#### Added

- Inactivity timeout option to download command for improved connection management
- Enhanced timeout configuration for HTTP client with better handling of stalled connections
- Updated default HTTP headers for improved content negotiation and security
- Memory optimization feature added through ChunkBuffer's reset_buffer method
- UnidentifiedFileSizeError exception for more graceful handling of unknown file sizes

#### Fixed

- Reduced maximum RAM usage constant from 30% to 20% for better system compatibility
- Enhanced file size input handling in download method
- Updated installation instructions for clarity
- Simplified downloader functionality for reliability

#### Dependencies

- Updated ruff to version 0.11.3
- Updated rich package to version 14.0.0
- Updated typing-extensions to version 4.13.0
- Updated pytest to version 8.3.5
- Updated typer to version 0.15.2
- Updated tenacity to version 9.1.2
- Updated pydantic to version 2.11.1
- Updated dependencies for anyio and iniconfig

## [0.5.1] - (Performance Enhancements & Stability Improvements)

#### Changed

- Streamlined HTTP client initialization and enhanced file info fetching logic
- Improved code readability by adjusting indentation in download_with_buffer_worker
- Updated RemoteFileInfo size type to allow "unknown" and improved URL validation
- Simplified Makefile commands and updated help text
- Updated project description to emphasize optimization features

#### Added

- Inactivity timeout configuration for HTTP client and improved timeout handling
- Updated default HTTP headers for enhanced content negotiation and security
- Reset_buffer method to ChunkBuffer for better memory management
- UnidentifiedFileSizeError exception for handling unknown file sizes

#### Fixed

- Reduced maximum RAM usage constant from 30% to 20% for better system compatibility

#### Dependencies

- Updated ruff to version 0.11.0
- Updated pytest to version 8.3.5
- Updated typer to version 0.15.2

## [0.5.0] - (Major Improvements & New Features)

#### Changed

- Migrated to httpx library for improved HTTP/2 support
- Optimized chunk size calculations for better performance
- Enhanced error handling and recovery mechanisms
- Improved progress bar responsiveness
- Updated dependencies and requirements

#### Added

- Advanced retry mechanisms with exponential backoff
- Adaptive chunk size based on connection speed
- Enhanced error messages and debugging information
- New connection pooling system

#### Fixed

- Memory management issues with large files
- Progress bar flickering during high-speed downloads
- Connection timeout handling
- Thread synchronization issues
- File corruption during interrupted downloads

#### Removed

- Legacy HTTP client implementation
- Deprecated connection handling methods
- Obsolete retry mechanisms
- Logger functionality

## [0.3.6] - (Bug Fixes & Performance Improvements)

#### Changed

- Updated CLI demo gif
- Updated Makefile

#### Added

- Added a new logger system (always log everything to a file, located at {TEMP_DIR}/turbodl.log)

#### Fixed

- Size formatting issues

#### Removed

- Unused constants
- --save-log-file CLI option
- assets directory

## [0.3.5] - (Performance & Stability Improvements)

#### Changed

- Moved all constants to a dedicated constants.py file
- Updated chunk buffer values
- Enhanced code typings
- Improved max connections calculator

#### Added

- Demo option for Makefile
- Signal handlers for graceful exit
- .turbodownload suffix to incomplete downloads
- DownloadInterruptedError exception
- Demo CLI gif for documentation

#### Fixed

- Hash checker improvements
- Wrong file path handling
- Various gitignore configurations
- Test files structure
- Code formatting with ruff linter
- Changed minimum "max connections" to 2 instead of 4
- Enhanced chunk range generator
- Increased keepalive time and reduced max connections to 24
- Various CLI options and configurations

## [0.3.4] - (Hotfixes)

#### Changed

- Updated documentation by adding a demo gif demonstrating the TurboDL functionality

#### Added

- Missing hash verification feature
- Automatic retries on connection errors

#### Fixed

- Fixed release workflow
- Fixed CLI argument names and their values

## [0.3.3] - (Bug Fixes & Performance Improvements)

#### Changed

- Refactored and simplified entire code structure
- Updated CI workflow

#### Removed

- Removed unnecessary docstrings from internal functions

#### Fixed

- Fixed release workflow
- Fixed CLI argument names

## [0.3.2] - (New Features & Bug Fixes)

#### Changed

- Refactored and simplified several docstrings

#### Added

- Smart retry system for downloads and connections
- Added a new logger system
- Added logger option (--save-logfile) to CLI

#### Removed

- Removed unnecessary docstrings from internal functions

#### Fixed

- Fixed release workflow

## [0.3.1] - (Bug Fixes & Performance Improvements)

#### Changed

- Overall code structure and organization

#### Added

- Redirect handler implemented
- Updated CI workflow

#### Removed

- Removed unnecessary arguments from internal functions

#### Fixed

- Typo in documentation
- Release workflow issues

## [0.3.0] - (Enhanced Progress Bar & Code Optimization)

#### Changed

- Moved timeout parameter to .download() function for better control
- Relocated functions outside main code for improved structure
- Enhanced Rich library integration
- Improved CI/CD workflows
- Simplified documentation structure
- Updated EditorConfig extensions
- Test suite performance
- Progress bar rendering efficiency
- Package building process
- Overall code structure and organization

#### Added

- Completely redesigned progress bar with enhanced visual feedback
- Custom time elapsed and transfer speed columns
- Contributors section in documentation
- Automatic version checker for releases
- Comprehensive test suite with RAM buffer testing
- Missing RAM file system detection

#### Removed

- Unnecessary timeout parameter redundancy
- Functions nested inside other functions
- Clean option from Makefile commands
- Mypy checker (replaced by Ruff)

#### Fixed

- Version release verification system
- File name detection errors
- Various syntax and typing issues
- Non-buffered download functionality
- Multiple linting-related fixes

## [0.2.0] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.8] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.7] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.6] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.5] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.4] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.3] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.2] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.1] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.1.0] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.0.3] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.0.2] - ()

#### Changed

#### Added

#### Removed

#### Fixed

## [0.0.1] - (Initial Release)

#### Changed

#### Added

#### Removed

#### Fixed
