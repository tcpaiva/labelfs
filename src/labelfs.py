#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
import hashlib

from fuse import FUSE, FuseOSError, Operations


class OpenedFiles:
    def __init__(self, file_path, tmp_file):
        self.file_path = file_path
        self.tmp_file = tmp_file


class LabelFS(Operations):
    
    chmod = None
    chown = None
    mknod = None 
    
    def __init__(self, root_path, mnt_path):
        self.root_path = root_path
        self.mnt_path = mnt_path
        self.files_path = os.path.join(self.root_path, ".files")
        print("root:", self.root_path, "mnt:", self.mnt_path, "files:", self.files_path)

        try: 
            os.mkdir(self.files_path)
        except OSError:
            if not os.path.isdir(self.files_path):
                 raise
        
        self.labels_roll = []
        for item in os.listdir(self.root_path):
            if not item.startswith("."):
                curr_path = os.path.join(self.root_path, item)
                if os.path.isdir(curr_path):
                    self.labels_roll.append(item)
        print "labels:", self.labels_roll


    # Helpers
    # =======

    def _get_hash(self):
        pass

    def _full_path(self, partial):
        if partial.startswith(os.sep):
            partial = partial[1:]
        path = os.path.join(self.root_path, partial)
        return path

    def _get_components(self, path):
        head, file_name = os.path.split(path)
        relative_path = os.path.relpath(head, self.root_path)
        labels = relative_path.split(os.sep)
        return labels, file_name
    
    def _real_path(self, path):
        if path.startswith("/"):
            path = path[1:]
        head, file_name = os.path.split(path)
        real_path = os.path.join(self.root_path, file_name)
        return real_path
    
    def _labels(self, path):
        if path.startswith("/"):
            path = path[1:]
        head, tail = os.path.split(path)
        relative_path = os.path.relpath(head, self.root_path)
        labels = relative_path.split(os.sep)
        return labels

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print "access"

        path = path[1:] if path.startswith("/") else path
        print path

        others, label = os.path.split(path) 
        full_path = os.path.join(self.root_path, label)

        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)


    def getattr(self, path, fh=None):
        print "getattr"
        print "path:", path
        print "fh", fh

        # sanitize path
        path = path[1:] if path.startswith("/") else path
        print "path:", path

        # keys for stat
        keys = ['st_atime', 'st_ctime', 'st_gid', 'st_mode', 
                 'st_mtime', 'st_nlink', 'st_size', 'st_uid']

        # get the last field from path
        others, name = os.path.split(path)
        print "others:", others, "name:", name

        if others != "" and name not in self.labels_roll:
            labels = [x for x in others.split(os.sep) if x in self.labels_roll]
            print "labels:", labels
            target_path = os.path.join(self.root_path, labels[0], name)
        else:
            target_path = os.path.join(self.root_path, name)
        print "target_path:", target_path
        st = os.stat(target_path)            

        attr = dict((key, getattr(st, key)) for key in keys)
        print "attr:", attr

        return attr


    def readdir(self, path, fh):
        print "readdir"
        print "path:", path
        print "fh", fh

        # sanitize path
        path  = path[1:] if path.startswith("/") else path

        # break path into valid labels
        labels = [x for x in path.split(os.sep) if x in self.labels_roll]
        print "labels:", labels

        dirents = ['.', '..']

        # labels are always prepended in ls command
        available_labels = [x for x in self.labels_roll if x not in labels]
        print "available_labels:", available_labels
        dirents.extend(available_labels) 

        # get instersection of each label contents
        all_files = []
        for label in labels:
            label_path  = os.path.join(self.root_path, label)
            print "label_path:", label_path
            curr_files = os.listdir(label_path)
            print "curr_files:", curr_files
            all_files.append(curr_files)
            

        if len(all_files) == 0:
            files = []
        elif len(all_files) == 1:
            files = all_files[0]
        else:
            files = list(set.intersection(*map(set, all_files)))
        print "files:", files

        dirents.extend(files)
        print "dirents:", dirents
            
        for r in dirents:
            yield r

    def readlink(self, path):
        print "readlink"
        print "path:", path
        pathname = os.readlink(self._full_path(path))
        print "pathname:", pathname
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            print "sanitizing"
            return os.path.relpath(pathname, self.root)
        else:
            return pathname


    def rmdir(self, path):
        print "rmdir"

    def mkdir(self, path, mode):
        print "mkdir"
        print "path:", path
        
        # sanitize path
        path = path[1:] if path.startswith("/") else path

        # get name
        head, label_name = os.path.split(path)

        # always in root path
        label_path = os.path.join(self.root_path, label_name)
        print "label_path:", label_path

        # create directory
        re = os.mkdir(label_path, mode)
        print "return:", re
        
        # update list
        self.labels_roll.append(label_name)

        return re


    def statfs(self, path):
        print "statfs"

    def unlink(self, path):
        print "unlink"

    def symlink(self, target, name):
        print "symlink"

    def rename(self, old, new):
        print "rename"

    def link(self, target, name):
        print "link"

    def utimens(self, path, times=None):
        print "utimens"

    # File methods
    # ============

    def open(self, path, flags):
        print "open"

        # sanitize path
        path = path[1:] if path.startswith(os.sep) else path

        others, file_name = os.path.split(path)
        if others == "":
            raise FuseOSError(errno.EACCES)

        file_path = os.readlink(os.path.join(self.root_path, path))
        fh = os.open(file_path, flags)
        return fh


    def create(self, path, mode, fi=None):
        print "create"
        print "path:", path

        # sanitize path
        path = path[1:] if path.startswith(os.sep) else path

        others, file_name = os.path.split(path)
        if others == "":
            raise FuseOSError(errno.EACCES)

        file_path = os.path.join(self.files_path, file_name)
        return os.open(file_path, os.O_WRONLY | os.O_CREAT, mode)


    def read(self, path, length, offset, fh):
        print "read"
        print "path:", path
        print "fh:", fh
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)


    def write(self, path, buf, offset, fh):
        print "write"
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)


    def truncate(self, path, length, fh=None):
        print "truncate"

    def flush(self, path, fh):
        print "flush"

    def release(self, path, fh):
        print "release"
        print "path:", path
        print "fh:", fh

        # sanitize path
        path = path[1:] if path.startswith(os.sep) else path

        others, file_name = os.path.split(path)
        if others == "":
            raise FuseOSError(errno.EACCES)

        re = os.close(fh)

        old_path = os.path.join(self.files_path, file_name)
        print "old_path:", old_path

        unique = hashlib.sha256()
        with open(old_path,'rb') as f: 
            for chunk in iter(lambda: f.read(128 * unique.block_size), b''): 
                unique.update(chunk)
        new_path = os.path.join(self.files_path, unique.hexdigest())
        print "new_path:", new_path

        os.rename(old_path, new_path)

        labels = [x for x in path.split(os.sep) if x in self.labels_roll]
        print "labels:", labels
        
        for label in labels:
            dest_path = os.path.join(self.root_path, label)
            relative_path = os.path.relpath(self.files_path, dest_path)
            tmp = os.path.join(dest_path, file_name)
            print "tmp:", tmp
            os.symlink(os.path.join(relative_path, unique.hexdigest()), tmp)

        return re


    def fsync(self, path, fdatasync, fh):
        print "fsync"


def main(mountpoint, root):
    FUSE(LabelFS(root, mountpoint), mountpoint, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
