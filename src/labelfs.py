#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations


class LabelFS(Operations):
    
    chmod = None
    chown = None
    mknod = None 
    
    def __init__(self, root):
        self.root = root
        print "root:", self.root
        self.all_files_label = "all_files"
        all_files_path = os.path.join(self.root, self.all_files_label)
        try: 
            os.mkdir(all_files_path)
        except OSError:
            if not os.path.isdir(all_files_path):
                raise
        
        labels = []
        for i in os.listdir(self.root):
            if os.path.isdir(os.path.join(self.root, i)):
                labels.append(i)
        print "labels:", labels
    
                    

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith(os.sep):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def _get_components(self, path):
        head, file_name = os.path.split(path)
        relative_path = os.path.relpath(head, self.root)
        labels = relative_path.split(os.sep)
        return labels, file_name
    
    def _real_path(self, path):
        if path.startswith("/"):
            path = path[1:]
        head, file_name = os.path.split(path)
        real_path = os.path.join(self.root, file_name)
        return real_path
    
    def _labels(self, path):
        if path.startswith("/"):
            path = path[1:]
        head, tail = os.path.split(path)
        relative_path = os.path.relpath(head, self.root)
        labels = relative_path.split(os.sep)
        return labels

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print "access"

    def getattr(self, path, fh=None):
        print "getattr"
        print "path:", path
        print "fh", fh
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        print "readdir"
        print "path:", path
        print "fh", fh
        
        path  = path[1:] if path.startswith("/") else path
        labels = path.split(os.sep)

        contents = []
        for label in labels:
            label_path = os.path.join(self.root, label)
            content = os.listdir(label_path)
            contents.append(content)

        dirents = ['.', '..']
        dirents.extend(set.intersection(*map(set, contents)))
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
        head, tail = os.path.split(path)
        label_path = os.path.join(self.root, tail)
        print "label_path:", label_path
        re = os.mkdir(label_path, mode)
        print "return:", re

        labels = [d for d in os.listdir(self.root) if os.path.isdir(os.path.join(self.root, d))]
        print "labels:", labels
    
        for i in labels:
            print "i:", i
            if i != self.all_files_label:
                orig = os.path.join(self.root, i)
                print "orig:", orig
                for j in labels:
                    print "j:", j
                    if (i != j and j != self.all_files_label):
                        try:
                            target = os.path.join('..', j)
                            print "target:", target
                            link = os.path.join(orig, j)
                            print "link:", link
                            lh =  os.symlink(target, link)
                        except:
                            pass
                
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
        real_path = self._real_path(path)
        fh = os.open(real_path, flags)
        return fh

    def create(self, path, mode, fi=None):
        print "create"
        print "path:", path
        
        real_path = self._real_path(path)
        print "real_path:", real_path
        
        fh = os.open(real_path, os.O_WRONLY | os.O_CREAT, mode)
        print "fh:", fh
        
        
        full_path = self._full_path(path)
        fp_head, file_name = os.path.split(full_path)
        print "fp_head:", fp_head
        labels = fp_head.split(os.sep)

        not_labels = self.root.split(os.sep)
        for not_label in not_labels:
            try:
                labels.remove(not_label)
            except:
                pass
        print "labels:", labels
        
        target = os.path.join('..', file_name)
        print "target:", target
        
        for label in labels:
            link = os.path.join(self.root, label, file_name)
            print "link:", link
            lh =  os.symlink(target, link)
            
        link = os.path.join(self.root, self.all_files_label, file_name)
        print "link:", link
        lh =  os.symlink(target, link)
        
        return fh

    def read(self, path, length, offset, fh):
        print "read"
        print "path:", path
        print "fh:", fh
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        print "write"

    def truncate(self, path, length, fh=None):
        print "truncate"

    def flush(self, path, fh):
        print "flush"

    def release(self, path, fh):
        print "release"
        print "path:", path
        print "fh:", fh
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        print "fsync"


def main(mountpoint, root):
    FUSE(LabelFS(root), mountpoint, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
