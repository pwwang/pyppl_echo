# pyppl_echo

Echo script output to PyPPL logs

- Echo stdout/stderr with filters
- Log specific infomation in PyPPL log

## Installation
```shell
pip install pyppl_echo
```

## Usage

```python
# only echo first job
PyPPL(config_echo_jobs = 0)
# echo first 3 jobs
PyPPL(config_echo_jobs = '0-2')
PyPPL(config_echo_jobs = '0,1,2')
PyPPL(config_echo_jobs = [0,1,2])
# only echo stdout
PyPPL(config_echo_jobs = 0, config_echo_types = 'stdout')
# echo all
PyPPL(config_echo_jobs = 0, config_echo_types = 'all')
# echo with filter
# lines startswith 'DEBUG'
PyPPL(config_echo_jobs = 0, config_echo_types = {'stderr': r'^DEBUG'})

# log message to PyPPL log
PyPPL(config_echo_jobs = 0, config_echo_types = {'stderr': r'^pyppl.logger'})
# in your script
# sys.stderr.write('pyppl.logger: debug infomation')
# with log leve
# sys.stderr.write('pyppl.logger.debug: debug infomation')

```
