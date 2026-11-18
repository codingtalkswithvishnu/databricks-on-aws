-- Read in the actual intended workspace; values depend on the active session.
-- Successful context discovery does not prove write rights or source access.
SELECT current_user() AS execution_user,
       current_catalog() AS default_catalog,
       current_schema() AS default_schema;
