## 工具使用说明

| 名称 | 说明 |
| --- | --- |
| upload_to_sftp.py | 自动将多个目录进行压缩，并通过sftp上传到相应的主机上。<br> python upload_to_sftp.py --src-list `src1` `src2` --dist-dir `test_dir` --name-prefix `test_backup` --host `目标主机IP` --user `sftp用户` --password `sftp密码` |