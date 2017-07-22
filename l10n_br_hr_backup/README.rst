.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================
l10n_br Hr Backup
=================

This module allow backup salary rules and payroll structures


Installation
============

This module depends on :

l10n_br_hr_payroll


Configuration
=============


Usage
=====

Este módulo faz backup de tres modelos:

- hr.salary.rule
- hr.payroll.structure
- hr.salary.rule.category

Após instalado o modulo, navegar até o menu de backup em:

 Recursos Humanos > Configurações > HR Backup

Em seguida Confirmar o backup.


A rotina de backup consiste em varrer o sistema, identificar todas as regras de salarios,
 estruturas de salario e categorias de salarios que foram criadas ou editadas via interface
 e escrever em arquivos XML que estão pre-estabelecidos na pasta data do próprio modelo.


Estrutura de arquivos:

.. image:: /l10n_br_hr_backup/static/description/tree_files.png



For further information, please visit:

 * https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

 * no known issues


Credits
=======

Contributors
------------

* Hendrix Costa <hendrix.costa@kmee.com.br>


Maintainer
----------

.. image:: http://www.abgf.gov.br/wp-content/themes/abgf/images/header-logo.png
   :alt: ABGF
   :target: http://www.abgf.gov.br
