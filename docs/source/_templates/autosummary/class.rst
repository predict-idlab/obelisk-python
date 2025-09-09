{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :show-inheritance:

   {% block methods %}
   .. automethod:: __init__
      :no-index:

   {% if methods %}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
   {% for item in methods %}
   {% if item not in inherited_members %}
   .. automethod:: {{ item }}
      :no-index-entry:
   {%- endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
   {% if item not in inherited_members %}
   .. autoattribute:: {{ item }}
      :no-index-entry:
   {%- endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}
