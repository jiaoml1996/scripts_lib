import argparse
import os
import shutil
import tarfile
import tempfile
import time

import paramiko


class Backup:
    def __init__(self,
                 src_list=[],
                 dist_dir=None,
                 dist_name_prefix=None,
                 sftp_info=None,
                 keep_num=7):
        assert len(src_list) > 0
        assert dist_dir
        assert dist_name_prefix
        assert sftp_info

        self.src_list = src_list
        self.dist_dir = dist_dir
        self.dist_name_prefix = dist_name_prefix
        self.sftp_host = sftp_info['host']
        self.sftp_port = 22
        self.sftp_user = sftp_info['user']
        self.sftp_password = sftp_info['password']
        self.keep_num = keep_num

        self.current_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())

        # 获取临时文件
        self.tempdir = os.path.join(tempfile.gettempdir(),
                                    f"backup_{self.current_time}")
        if not os.path.exists(self.tempdir):
            os.makedirs(self.tempdir)
        self.filename = f"{self.dist_name_prefix}_{self.current_time}.tar.gz"
        self.tmp_filename_full_path = os.path.join(self.tempdir, self.filename)

    def compress(self):
        # 对src_list中的数据进行压缩
        print(f"temp file:{self.tmp_filename_full_path}")
        with tarfile.open(self.tmp_filename_full_path, 'w') as f:
            for src in self.src_list:
                if os.path.isfile(src):
                    f.add(src, arcname=src)
                else:
                    for root, dirs, files in os.walk(src):
                        for single_file in files:
                            full_path = os.path.join(root, single_file)
                            f.add(full_path)

    def upload_to_ftp(self):
        # connect to sftp
        sf = paramiko.Transport((self.sftp_host, self.sftp_port))
        sf.connect(username=self.sftp_user, password=self.sftp_password)
        sftp = paramiko.SFTPClient.from_transport(sf)

        # remote is exists?
        try:
            sftp.mkdir(self.dist_dir)
        except:
            pass
        remotepath = os.path.join(self.dist_dir, self.filename)
        sftp.put(localpath=self.tmp_filename_full_path, remotepath=remotepath)
        print(f"backup file upload {remotepath} successfully")

        # get all files of the remote dir
        filenames = sftp.listdir(self.dist_dir)

        # filiter the files which is not end with ".tar"
        filenames = list(filter(lambda x: '.tar' in x, filenames))

        # sort all files according to the create time
        filenames = [[
            filename,
            int(''.join(filename.split('.')[0].split('_')[-2:]))
        ] for filename in filenames]
        filenames = sorted(filenames, key=lambda x: x[-1], reverse=True)
        remove_filenames = filenames[self.keep_num:]
        for filename, _ in remove_filenames:
            sftp.remove(os.path.join(self.dist_dir, filename))
        print(f"keep the new [{self.keep_num}] files")
        sftp.close()

    def run(self):
        print("start compress all files")
        self.compress()
        print("compress all files successfully")

        print("start upload compressed file")
        self.upload_to_ftp()
        print("upload compressed file successfully")

        self.clear()

    def clear(self):
        shutil.rmtree(self.tempdir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Arguments")
    parser.add_argument(
        "--src-list",
        type=str,
        nargs='+',
        required=True,
        help="src list, support multi path. eg. --src-list src1 src2")
    parser.add_argument("--dist-dir",
                        type=str,
                        required=True,
                        help="remote path")
    parser.add_argument(
        "--name-prefix",
        type=str,
        required=True,
        help="prefix name of the compress file, e.g. prefix_xxxxx_xxxxx.tar.gz"
    )
    parser.add_argument("--host",
                        type=str,
                        required=True,
                        help="the host of the sftp")
    parser.add_argument("--user",
                        type=str,
                        required=True,
                        help="the user of the sftp")
    parser.add_argument("--password",
                        type=str,
                        required=True,
                        help="the password of the sftp")
    args = parser.parse_args()
    bk = Backup(src_list=args.src_list,
                dist_dir=args.dist_dir,
                dist_name_prefix=args.name_prefix,
                sftp_info={
                    'host': args.host,
                    'user': args.user,
                    'password': args.password
                })
    bk.run()