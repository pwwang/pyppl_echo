"""Echoing job script outputs to PyPPL logs"""
import re
from pyppl.plugin import hookimpl
from pyppl.utils import always_list

__version__ = "0.0.4"


def expand_numbers(numbers):
    """
    Expand a descriptive numbers like '0,3-5,7' into read numbers:
    [0,3,4,5,7]
    @params:
        numbers (str): The string of numbers to expand.
    @returns:
        (list) The real numbers
    """
    numberstrs = always_list(numbers)
    numbers = []
    for numberstr in numberstrs:
        if '-' not in numberstr:
            numbers.append(int(numberstr))
        else:
            numstart, numend = numberstr.split('-')
            numbers.extend(range(int(numstart), int(numend) + 1))
    return numbers


def fileflush(filed, residue, end=False):
    """
    Flush a file descriptor
    @params:
        `filed`  : The file handler
        `residue`: The remaining content of last flush
        `end`    : The file ends? Default: `False`
    """
    filed.flush()
    # OSX cannot tell the pointer automatically
    filed.seek(filed.tell())
    lines = filed.readlines() or []
    if lines:
        lines[0] = residue + lines[0]
        residue = '' if lines[-1].endswith('\n') else lines.pop(-1)
        if residue and end:
            lines.append(residue + '\n')
            residue = ''
    elif residue and end:
        lines.append(residue + '\n')
        residue = ''
    return lines, residue


def flush(job, end=False):  # pylint: disable=too-many-branches
    """
    Flush stdout/stderr
    @params:
        `fout`: The stdout file handler
        `ferr`: The stderr file handler
        `lastout`: The leftovers of previously readlines of stdout
        `lasterr`: The leftovers of previously readlines of stderr
        `end`: Whether this is the last time to flush
    """
    if job.index not in job.proc.config.echo_jobs:
        return

    if not job.config.echo_fout or job.config.echo_fout.closed:
        job.config.echo_fout = (job.dir / 'job.stdout').open()
    if not job.config.echo_ferr or job.config.echo_ferr.closed:
        job.config.echo_ferr = (job.dir / 'job.stderr').open()
    outfilter = job.proc.config.echo_types.get('stdout', '__noout__')
    errfilter = job.proc.config.echo_types.get('stderr', '__noerr__')

    if outfilter != '__noout__':
        lines, job.config.echo_lastout = fileflush(job.config.echo_fout,
                                                   job.config.echo_lastout,
                                                   end)
        for line in lines:
            if not outfilter or re.search(outfilter, line):
                job.logger(line.rstrip('\n'), level='stdout', plugin='echo')
    lines, job.config.echo_lasterr = fileflush(job.config.echo_ferr,
                                               job.config.echo_lasterr, end)
    for line in lines:
        if line.startswith('pyppl.logger'):
            logstr = line.rstrip('\n')[12:].lstrip()
            if ':' not in logstr:
                logstr += ':'
            loglevel, logmsg = logstr.split(':', 1)
            loglevel = loglevel[1:] if loglevel else 'log'
            # '_' makes sure it's not filtered by log levels
            job.logger(logmsg.lstrip(), level='_' + loglevel, plugin='echo')
        elif errfilter != '__noerr__':
            if not errfilter or re.search(errfilter, line):
                job.logger(line.rstrip('\n'), level='stderr', plugin='echo')

    if end and job.config.echo_fout and not job.config.echo_fout.closed:
        job.config.echo_fout.close()
    if end and job.config.echo_ferr and not job.config.echo_ferr.closed:
        job.config.echo_ferr.close()


def echo_jobs_converter(jobs):
    """Convert job indexes"""
    if not jobs and jobs != 0:
        return []
    if isinstance(jobs, int):
        return [jobs]
    if isinstance(jobs, str):
        return expand_numbers(jobs)
    return list(jobs)


def echo_types_converter(types):
    """Convert job types"""
    if not types:
        return {'stdout': None, 'stderr': None}
    if not isinstance(types, dict):
        types = {types: None}
    if 'all' in types:
        return {'stdout': types['all'], 'stderr': types['all']}
    return types


@hookimpl
def logger_init(logger):
    """Add log levels"""
    logger.add_level('STDOUT')
    logger.add_level('STDERR')


@hookimpl
def setup(config):
    """Add default configs"""
    config.config.echo_jobs = []
    config.config.echo_types = ''


@hookimpl
def proc_init(proc):
    """Add config"""
    proc.add_config('echo_jobs', converter=echo_jobs_converter)
    proc.add_config('echo_types', converter=echo_types_converter)


@hookimpl
def job_init(job):
    """Add job configs"""
    job.add_config('echo_fout')
    job.add_config('echo_ferr')
    job.add_config('echo_lastout', '')
    job.add_config('echo_lasterr', '')


@hookimpl
def job_poll(job, status):
    """Do it will polling the job"""
    flush(job, end=status == 'done')
