{ pkgs, ... }:

{
  # https://devenv.sh/basics/
  env.DJANGO_SETTINGS_MODULE = "babybuddy.settings.development";

  # https://devenv.sh/packages/
  packages = [
    pkgs.pipenv
    pkgs.nodejs_18
    pkgs.nodePackages.gulp
  ];

  # https://devenv.sh/scripts/

  enterShell = ''
    pipenv install --dev
    npm i
    gulp migrate
    gulp
  '';

  # https://devenv.sh/languages/
  languages.python.enable = true;
  languages.javascript = {
    enable = true;
    npm.install.enable = true;
  };

  devcontainer = {
    enable = true;
    settings.customizations.vscode.extensions = [
      "bbenoist.Nix"
      "ms-python.python"
      "batisteo.vscode-django"
    ];
  };

  # services.nginx.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
