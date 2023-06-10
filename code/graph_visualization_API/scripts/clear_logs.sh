# ensure the CWD is the directory of this script
script_dir="$(dirname $0)"
cd $script_dir

cd ../logs  # log directory
rm ./*.log  # remove all log files
