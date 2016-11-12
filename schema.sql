drop table if exists virtual_users;
create table usermap (
  id integer primary key autoincrement,
  xmpp_user text not null,
  matrix_user text not null
);
create table roommap (
  id integer primary key autoincrement,
  xmpp_room text not null,
  matrix_room text not null
);
create table room_membership (
  id integer primary key autoincrement,
  room text not null,
  room integer not null
)
