{ pkgs, ... }:

{
  # https://devenv.sh/basics/
  env.DJANGO_SETTINGS_MODULE = "babybuddy.settings.development";

  # https://devenv.sh/packages/
  packages = [
    pkgs.pipenv
    pkgs.python311
    pkgs.nodejs_18
    pkgs.glibc
  ];

  # https://devenv.sh/scripts/

  enterShell = ''
    pipenv install --dev
    npm i
    npx gulp migrate
    npx gulp
  '';

  # https://devenv.sh/languages/
  languages.python.enable = true;
  languages.javascript = {
    enable = true;
    npm.install.enable = true;
  };

  devcontainer.enable = true;

  # services.nginx.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
