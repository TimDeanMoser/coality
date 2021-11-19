# Comment-Quality
Install all modules required with 'pip install -r requirements.txt' and install srcML to your PATH. Tested and developed on Windows and **Python 3.8**

If using Linux (tested on Ubuntu), run the `setup.sh` script to port the project over and handle all requirements. This will allow you to work with main.py right away, to generate an output.json file from a downloaded test project. 

If using Windows, run the `setup.ps1` script to quickly get up and running with the project.

Please note the following:

* For fasttext, install the following: `Windows Universal C Runtime`, `Windows 10 SDK (10.x.x.x)`, and `C++ Build Tools core features`
* The project should be permanently added to `PYTHONPATH` in `Environment Variables` i.e., `C:\PathtoPython38;C:\PathtoProject`

**Example usage**:
`python .\quality_assessment\src\main.py C:\Full\Path\To\Example_Project .\outputs\example_output.json .\models\ -log debug`

All runnable files...
- predictor
- trainer
- validator
- comment_evaluator
- rater
- main

...can and should be run through CMD with proper arguments. If you struggle with a certain one, try calling --help or
read the docstring of the script.

For smooth performance, make sure that the root of the repository is the working directory when running any script
and use absolute paths as the arguments.

### License

Coality is licensed under the GNU Affero General Public License. Every file should include a license header, if not, the following applies:

```
Coality automatically predicts and labels comment types and assess their quality.
Copyright (C) 2021-today  Tim Moser & Sebastiano Panichella

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. 
```

Carefully read the [full license agreement](https://www.gnu.org/licenses/agpl-3.0.en.html).

> "... [The AGPL-3.0 license] requires the operator of a network server to provide the source code of the modified version running there to the users of that server."
