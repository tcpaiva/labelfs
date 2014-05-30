labelfs
=======

Labelfs is a (one more) tag filesystem under development using FUSE and Python (based on fusepy). This fs aims to implement a tag tool completely transparent to operating system, i. e. any program will work as it was specified without worries about file manipulation.


Specification
=============

* A label is a directory (mkdir is enough).
* From any label you will can access all the others but labels in the current path. Side effect: files and labels could not have same name (there is no way to distinguish one of another).
* Files exist in only one place (directory), named here as "repository". Side effect: files could not have same name.
* A file exist only one time in repository, i. e.: if identical files just result in links to a file. 
* Put files under labels (i. e. in a directory) only add links to files in repository.
* Files in root path of the mount point are uncategorized.
* At this moment I don't get any reason to work with "hidden labels". This way, hidden directories at root path are used to management functions.
* Copy from or to mount point is enough to adapt a tree into labelfs system.


Examples
========

```
mountpoint $ touch f
mountpoint $ ls
f
mountpoint $ mkdir d0
mountpoint $ cd d0
mountpoint/d0 $ touch f0
mountpoint/d0 $ ls
f0
mountpoint/d0 $ mkdir d1
mountpoint/d0 $ ls
d1 f0
mountpoint/d0 $ cd d1
mountpoint/d0/d1 $ touch f01
mountpoint/d0/d1 $ mkdir d2
mountpoint/d0/d1 $ ls
d2 f01
mountpoint/d0/d1 $ cd d2
mountpoint/d0/d1/d2 $ touch f012
mountpoint/d0/d1/d2 $ ls
f012
mountpoint/d0/d1/d2 $ cd ..
mountpoint/d0/d1 $ ls
d2 f01 f012
mountpoint/d0/d1 $ cd ..
mountpoint/d0 $ ls
d1 d2 f0 f01 f012 
mountpoint/d0 $ cd ..
mountpoint $ ls
d0 d1 d2 f
mountpoint $ cd d1
mountpoint/d1 $ touch f1
mountpoint/d1 $ ls
d0 d2 f01 f012 f1
mountpoint/d1 $ cd d2
mountpoint/d1/d2 $ touch f12
mountpoint/d1/d2 $ ls
d0 f012 f12
mountpoint/d1/d2 $ cd d0
mountpoint/d1/d2/d0 $ ls
f012
mountpoint/d1/d2/d0 $ cd ../../..
mountpoint $ ls d0
d1 d2 f0 f01 f012
mountpoint $ ls d1
d0 d2 f01 f012 f1 f12 
mountpoint $ ls d2
d0 d1 f012 f12
mountpoint $ ls d0/d1
d2 f01 f012
mountpoint $ ls d1/d2
d0 f12 f012
mountpoint $ ls d1/d0/d2
f012
mountpoint $ ls
d0 d1 d2 f
```

Design
======

Expected result
---------------

```
mount_point\
        file
        dir_0\
                file_0
                file_01
                file_02
                file_012
        dir_1\
                file_1
                file_01
                file_12
                file_012
        dir_2\
                file_2
                file_02
                file_12
                file_012
```

Structure
---------

```
labelfs_root\
        .files\
                file -------------------------------------+
                file_0 -----------+                       |
                file_01 ----------|-+-------+             |
                file_012 ---------|-|---+---|---+-------+ |
                file_02 ----------|-|-+-|---|---|---+   | |
                file_1 -----------|-|-|-|-+ |   |   |   | |
                file_12 ----------|-|-|-|-|-|-+-|---|-+ | |
                file_2 -----------|-|-|-|-|-|-|-|-+ | | | |
        dir_0\                    | | | | | | | | | | | | |
                link_to_file_0 ---+ | | | | | | | | | | | |
                link_to_file_01 ----+ | | | | | | | | | | |
                link_to_file_02 ------+ | | | | | | | | | |
                link_to_file_012 -------+ | | | | | | | | |
        dir_1\                            | | | | | | | | |
                link_to_file_1 -----------+ | | | | | | | |
                link_to_file_01 ------------+ | | | | | | |
                link_to_file_12 --------------+ | | | | | |
                link_to_file_012 ---------------+ | | | | |
        dir_2\                                    | | | | |
                link_to_file_2 -------------------+ | | | |
                link_to_file_02 --------------------+ | | |
                link_to_file_12 ----------------------+ | |
                link_to_file_012 -----------------------+ |
        file ---------------------------------------------+
```

