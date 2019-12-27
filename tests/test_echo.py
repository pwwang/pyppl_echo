import pytest
from diot import Diot
from pyppl import Proc
from pyppl.job import Job
from pyppl.utils import fs
from pyppl.logger import logger, LEVEL_GROUPS
from pyppl_echo import expand_numbers, fileflush, echo_jobs_converter, echo_types_converter, flush, logger_init, job_poll

@pytest.fixture
def fd_fileflush(tmp_path):
	tmpfile = tmp_path / 'fileflush.txt'
	tmpfile.write_text('')
	with open(tmpfile, 'r') as fd_read, open(tmpfile, 'a') as fd_append:
		yield fd_read, fd_append

@pytest.fixture(params = range(5))
def fixt_fileflush(request, fd_fileflush):
	fd_read, fd_append = fd_fileflush
	if request.param == 0:
		return Diot(filed = fd_read, residue = '', expt_lines = [], expt_residue = '')
	if request.param == 1:
		fd_append.write('abcde')
		fd_append.flush()
		return Diot(filed = fd_read, residue = '', expt_lines = [], expt_residue = 'abcde')
	if request.param == 2:
		fd_append.write('ccc\ne1')
		fd_append.flush()
		return Diot(filed = fd_read, residue = 'abcde', expt_lines = ['abcdeccc\n'], expt_residue = 'e1')
	if request.param == 3:
		fd_append.write('ccc')
		fd_append.flush()
		return Diot(filed = fd_read, residue = '', end = True, expt_lines = ['ccc\n'], expt_residue = '')
	if request.param == 4:
		return Diot(filed = fd_read, residue = 'end', end = True, expt_lines = ['end\n'], expt_residue = '')

@pytest.fixture
def job0(tmp_path):
	job = Job(0, Proc(
		workdir  = tmp_path/'pJob',
		dirsig   = True,
		config = Diot(echo_jobs=0, types='stderr')
	))
	# pretend it's running
	job.proc.runtime_config = {'dirsig': True}

	fs.mkdir(job.dir)
	(job.dir / 'job.script').write_text('')
	return job

@pytest.mark.parametrize('numbers,expt',[
	('1,2,3,4', [1,2,3,4]),
	('1-4', [1,2,3,4]),
	('1-4,7,8-10', [1,2,3,4,7,8,9,10]),
])
def test_expand_numbers(numbers, expt):
	assert expand_numbers(numbers) == expt

def test_fileflush(fixt_fileflush):
	lines, residue = fileflush(
		fixt_fileflush.filed, fixt_fileflush.residue, fixt_fileflush.get('end', False))
	assert lines == fixt_fileflush.expt_lines
	assert residue == fixt_fileflush.expt_residue

@pytest.mark.parametrize('jobs,expected', [
	([], []),
	([0,1], [0,1]),
	(0, [0]),
	('0,1', [0,1]),
])
def test_echo_jobs_converter(jobs, expected):
	assert echo_jobs_converter(jobs) == expected

@pytest.mark.parametrize('types,expected', [
	('', {'stderr': None, 'stdout': None}),
	('stderr', {'stderr': None}),
	({'all': '^log'}, {'stderr': '^log', 'stdout': '^log'}),
])
def test_echo_types_converter(types, expected):
	assert echo_types_converter(types) == expected


def test_flush(job0, caplog):
	job0.proc.config.echo_jobs = [1]
	flush(job0)
	assert '' == caplog.text
	assert job0.config.echo_lastout == ''
	assert job0.config.echo_lasterr == ''

	job0.proc.config.echo_jobs = [0]
	job0.proc.config.echo_types = {
		'stdout': '', 'stderr': r'^[^&].+$'}
	(job0.dir / 'job.stdout').write_text('out: line1\nout: line2')
	(job0.dir / 'job.stderr').write_text('err: line1\nerr: line2')
	caplog.clear()
	flush(job0)
	assert 'out: line1' in caplog.text
	assert 'err: line1' in caplog.text
	assert 'line2' not in caplog.text
	assert job0.config.echo_lastout == 'out: line2'
	assert job0.config.echo_lasterr == 'err: line2'

	(job0.dir / 'job.stderr').write_text(
		'err: line1\nerr: line23\n& ignored\npyppl.logger.abc\npyppl.logger.msg: hello world!')
	caplog.clear()
	job_poll(job0, status = 'done')
	#flush(job0, end = True)
	assert 'err: line23' in caplog.text
	assert '_MSG' in caplog.text
	assert '_ABC' in caplog.text
	assert 'hello world' in caplog.text
	assert 'ignored' not in caplog.text
	assert job0.config.echo_lastout == ''
	assert job0.config.echo_lasterr == ''

def test_hook():
	logger_init(logger)
	assert 'STDOUT' in LEVEL_GROUPS['INFO']
	assert 'STDERR' in LEVEL_GROUPS['INFO']
