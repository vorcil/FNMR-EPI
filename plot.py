import pyplot as plt
import numpy as np

 def build_step(self):
"""Build and install WRF and testcases using provided compile script."""
# enable parallel build
p = self.cfg['parallel']
self.par = ""
if p:
self.par = "-j %s" % p
# build wrf (compile script uses /bin/csh )
cmd = "tcsh ./compile %s wrf" % self.par
run_cmd(cmd, log_all=True, simple=True, log_output=True)
# build two testcases to produce ideal.exe and real.exe
for test in ["em_real", "em_b_wave"]:
cmd = "tcsh ./compile %s %s" % (self.par, test)
run_cmd(cmd, log_all=True, simple=True, log_output=True)
def test_step(self):
"""Build and run tests included in the WRF distribution."""
if self.cfg['runtest']:
# get list of WRF test cases
self.testcases = []
try:
self.testcases = os.listdir('test')
except OSError, err:
raise EasyBuildError("Failed to determine list of test cases: %s", err)
# exclude 2d testcases in non-parallel WRF builds
if self.cfg['buildtype'] in self.parallel_build_types:
self.testcases = [test for test in self.testcases if not "2d_" in test]
# exclude real testcases
self.testcases = [test for test in self.testcases if not test.endswith("_real")]
self.log.debug("intermediate list of testcases: %s" % self.testcases)
# exclude tests that should not be run
for test in ["em_esmf_exp", "em_scm_xy", "nmm_tropical_cyclone"]:
if test in self.testcases:
self.testcases.remove(test)
# some tests hang when WRF is built with Intel compilers
if self.comp_fam == toolchain.INTELCOMP: #@UndefinedVariable
for test in ["em_heldsuarez"]:
if test in self.testcases:
self.testcases.remove(test)
# determine parallel setting (1/2 of available processors + 1)
n = self.cfg['parallel'] / 2 + 1
# prepare run command
# stack limit needs to be set to unlimited for WRF to work well
if self.cfg['buildtype'] in self.parallel_build_types:
test_cmd = "ulimit -s unlimited && %s && %s" % (self.toolchain.mpi_cmd_for("./ideal.exe", 1),
self.toolchain.mpi_cmd_for("./wrf.exe", n))
else:
test_cmd = "ulimit -s unlimited && ./ideal.exe && ./wrf.exe" % n
def run_test():
"""Run a single test and check for success."""
# regex to check for successful test run
re_success = re.compile("SUCCESS COMPLETE WRF")
# run test
run_cmd(test_cmd, log_all=True, simple=True)
# check for success
fn = "rsl.error.0000"
try:
f = open(fn, "r")
txt = f.read()
f.close()
except IOError, err:
raise EasyBuildError("Failed to read output file %s: %s", fn, err)
if re_success.search(txt):
self.log.info("Test %s ran successfully." % test)
else:
raise EasyBuildError("Test %s failed, pattern '%s' not found.", test, re_success.pattern)
# clean up stuff that gets in the way
fn_prefs = ["wrfinput_", "namelist.output", "wrfout_", "rsl.out.", "rsl.error."]
for f in os.listdir('.'):
for p in fn_prefs:
if f.startswith(p):
os.remove(f)
self.log.debug("Cleaned up file %s." % f)

# The date of the WRF simulation file
date = '2015-07-15'

# The number of time steps in the WRF simulation
Nt = 73

# use 'l' for faster response, use 'h' for high resolution
mapResolution = 'h'

# This defines the grid box for which skewT-plots etc are based
lat_focuspoint = 60.2
lon_focuspoint = 11.08

# Additional grid point that will be marked by a red dot on some of the maps
# (set to -1 to avoid this red dot!)
lat_rg = 59.37
lon_rg = 10.78

# P_top must be the same as what is used in the WRF simulation
P_top = 10**4

P_bot = 10**5

# Max height used on z-axis for xz-plots
z_max = 4000.0

# Tick increment used for xz-plot
dz = 200

# Max height used when plotting terrain contours
max_h = 800

# Pressure interval used when plotting contour lines on top level map
pmsl_int = np.arange(960.,1040.,4)

# Temperature interval used when plotting contour lines
temp_int = np.arange(-80.0,50.0,2.0)

# levels used for xz-cloud plots
xz_cloudwater_levels = np.arange(0.08, 0.7, 0.08)
xz_rain_levels = np.arange(0.003, 0.0110, 0.0015)
xz_snow_levels = np.arange(0.06, 0.17, 0.02)

# levels used for tz-cloud plots
tz_cloudwater_levels = np.arange(0.08, 0.7,0.08)
tz_rain_levels = np.arange(0.003, 0.0110, 0.0015)
tz_snow_levels = np.arange(0.02, 0.10, 0.02)

WaterColor = "#B2FFFF"
LandColor = "#FFCCB9"
barb_increments = {'half': 2.5,'full':5.0,'flag':25.0}

cmap_red = plt.get_cmap('Reds')
cmap_green = plt.get_cmap('Greens')
cmap_blue = plt.get_cmap('Blues')
cmap_grey = plt.get_cmap('Greys')
cmap_jet = plt.get_cmap('Jet')



T_base = 300.0
T_zero = 273.15
L = 2.501e6 # latent heat of vaporization
R = 287.04  # gas constant air
Rv = 461.5  # gas constant vapor
eps = R/Rv
cp = 1005.
cv = 718.
kappa = (cp-cv)/cp
g = 9.81


 # build an run each test case individually
for test in self.testcases:
self.log.debug("Building and running test %s" % test)
#build_and_install
cmd = "tcsh ./compile %s %s" % (self.par, test)
run_cmd(cmd, log_all=True, simple=True)
# run test
try:
os.chdir('run')
if test in ["em_fire"]:
# handle tests with subtests seperately
testdir = os.path.join("..", "test", test)
for subtest in [x for x in os.listdir(testdir) if os.path.isdir(x)]:
subtestdir = os.path.join(testdir, subtest)
# link required files
for f in os.listdir(subtestdir):
if os.path.exists(f):
os.remove(f)
os.symlink(os.path.join(subtestdir, f), f)
# run test
run_test()
else:
# run test
run_test()
os.chdir('..')
except OSError, err:
raise EasyBuildError("An error occured when running test %s: %s", test, err)
# building/installing is done in build_step, so we can run tests
def install_step(self):
"""Building was done in install dir, so nothing to do in install_step."""
pass
def sanity_check_step(self):
"""Custom sanity check for WRF."""
mainver = self.version.split('.')[0]
self.wrfsubdir = "WRFV%s" % mainver
fs = ["libwrflib.a", "wrf.exe", "ideal.exe", "real.exe", "ndown.exe", "nup.exe", "tc.exe"]
ds = ["main", "run"]
custom_paths = {
'files': [os.path.join(self.wrfsubdir, "main", x) for x in fs],
'dirs': [os.path.join(self.wrfsubdir, x) for x in ds]
}
super(EB_WRF, self).sanity_check_step(custom_paths=custom_paths)
def make_module_req_guess(self):
mainver = self.version.split('.')[0]
self.wrfsubdir = "WRFV%s"%mainver
maindir = os.path.join(self.wrfsubdir, "main")
return {
'PATH': [maindir],
'LD_LIBRARY_PATH': [maindir],
'MANPATH': [],
}
def make_module_extra(self):
"""Add netCDF environment variables to module file."""
txt = super(EB_WRF, self).make_module_extra()
txt += self.module_generator.set_environment('NETCDF', os.getenv('NETCDF'))
if os.getenv('NETCDFF', None) is not None:
txt += self.module_generator.set_environment('NETCDFF', os.getenv('NETCDFF'))
return txt
