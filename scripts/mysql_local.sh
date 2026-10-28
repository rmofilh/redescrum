#!/usr/bin/env bash
# Alternativa ao docker-compose: MySQL 8.0.22 (mesma versao do dump) em espaco de usuario.
# Uso: scripts/mysql_local.sh {install|init|start|stop|client}
set -euo pipefail
OPT=${MYSQL_OPT:-$HOME/.local/opt}
BASE=$OPT/mysql
LIBS=$OPT/mysql-libs
DATADIR=${MYSQL_DATADIR:-$HOME/.local/share/tawos-mysql}
SOCK=$DATADIR/mysql.sock
export LD_LIBRARY_PATH=$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
case "${1:-}" in
  install)
    mkdir -p "$OPT" "$LIBS"; cd "$OPT"
    curl -sSL -o mysql.tar.xz https://cdn.mysql.com/archives/mysql-8.0/mysql-8.0.22-linux-glibc2.17-x86_64-minimal.tar.xz
    tar xf mysql.tar.xz && rm mysql.tar.xz
    ln -sfn mysql-8.0.22-linux-glibc2.17-x86_64-minimal mysql
    # libaio (Arch) e shims ncurses5 -> ncursesw6, sem tocar no sistema
    tmp=$(mktemp -d); F=libaio-0.3.113-5-x86_64.pkg.tar.zst
    curl -sSL -o "$tmp/$F" "https://geo.mirror.pkgbuild.com/core/os/x86_64/$F"
    tar xf "$tmp/$F" -C "$tmp" && cp -a "$tmp"/usr/lib/libaio.so.1* "$LIBS"/ && rm -rf "$tmp"
    ln -sf /usr/lib/libncursesw.so.6 "$LIBS/libncurses.so.5"
    ln -sf /usr/lib/libncursesw.so.6 "$LIBS/libtinfo.so.5" ;;
  init)
    mkdir -p "$DATADIR"
    "$BASE/bin/mysqld" --no-defaults --initialize-insecure --basedir="$BASE" --datadir="$DATADIR/data" ;;
  start)
    "$BASE/bin/mysqld" --no-defaults --basedir="$BASE" --datadir="$DATADIR/data" \
      --socket="$SOCK" --port=3307 --bind-address=127.0.0.1 --mysqlx=OFF \
      --max_allowed_packet=1G --innodb_buffer_pool_size=1G --innodb_log_file_size=512M \
      --innodb_flush_log_at_trx_commit=2 --skip-log-bin --secure-file-priv= \
      --log-error="$DATADIR/error.log" --pid-file="$DATADIR/mysqld.pid" & disown
    for i in $(seq 60); do "$BASE/bin/mysqladmin" -uroot --socket="$SOCK" ping >/dev/null 2>&1 && break; sleep 1; done
    "$BASE/bin/mysql" -uroot --socket="$SOCK" -e "CREATE DATABASE IF NOT EXISTS TAWOS; CREATE USER IF NOT EXISTS 'tawos'@'%' IDENTIFIED BY 'tawos'; CREATE USER IF NOT EXISTS 'tawos'@'localhost' IDENTIFIED BY 'tawos'; GRANT ALL ON TAWOS.* TO 'tawos'@'%'; GRANT ALL ON TAWOS.* TO 'tawos'@'localhost';"
    echo "MySQL pronto em 127.0.0.1:3307 (usuario tawos / senha tawos)" ;;
  stop)
    "$BASE/bin/mysqladmin" -uroot --socket="$SOCK" shutdown ;;
  client)
    shift; exec "$BASE/bin/mysql" -uroot --socket="$SOCK" "$@" ;;
  *) echo "uso: $0 {install|init|start|stop|client}"; exit 1 ;;
esac
