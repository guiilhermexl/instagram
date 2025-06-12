<?php
  session_start();
  session_destroy();
  header('Location: ?route=home');
  exit();
  ?>