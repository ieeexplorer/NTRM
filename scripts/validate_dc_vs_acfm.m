function payload = validate_dc_vs_acfm(output_file, case_name, branch_indices)
%VALIDATE_DC_VS_ACFM Run selected case39 N-1 contingencies through AC-CFM.
%
% Run from the repository root after adding MATPOWER and AC-CFM to the MATLAB
% path:
%
%   addpath('scripts')
%   validate_dc_vs_acfm()
%
% The default contingencies are MATPOWER 1-based branch rows:
%   [1 6 15 26 36 41 46]
%
% Python uses zero-based branch IDs for the same rows, so subtract one when
% comparing these results with cascade_ml outputs.

if nargin < 1 || isempty(output_file)
    output_file = fullfile('cascade_ml', 'data', 'validation', 'acfm_case39_n1.json');
end
if nargin < 2 || isempty(case_name)
    case_name = 'case39';
end
if nargin < 3 || isempty(branch_indices)
    branch_indices = [1 6 15 26 36 41 46];
end

mpc = loadcase(case_name);
settings = get_default_settings();
settings.verbose = 0;

initial_contingencies = cell(numel(branch_indices), 1);
for idx = 1:numel(branch_indices)
    initial_contingencies{idx, 1} = branch_indices(idx);
end

raw_result = accfm_branch_scenarios(mpc, initial_contingencies, settings);

metadata = struct();
metadata.schema_version = '1.0';
metadata.case_name = case_name;
metadata.branch_index_base = 'MATPOWER_1_based';
metadata.python_branch_index_note = 'Subtract 1 to compare with cascade_ml branch IDs.';
metadata.selected_matpower_branch_ids = branch_indices;
metadata.generated_at_utc = char(datetime('now', 'TimeZone', 'UTC', ...
    'Format', 'yyyy-MM-dd''T''HH:mm:ss''Z'''));
metadata.matlab_version = version;
metadata.git_commit = current_git_commit();

scenarios = repmat(empty_scenario(), numel(branch_indices), 1);
for idx = 1:numel(branch_indices)
    matpower_branch_id = branch_indices(idx);
    python_branch_id = matpower_branch_id - 1;
    scenarios(idx).scenario_id = idx;
    scenarios(idx).contingency_key = sprintf('%d', python_branch_id);
    scenarios(idx).matpower_branch_id = matpower_branch_id;
    scenarios(idx).python_branch_id = python_branch_id;
    scenarios(idx).unserved_load_mw = numeric_field(raw_result, 'lost_load_final', idx);
    scenarios(idx).max_loading_ratio = first_available_numeric(raw_result, idx, ...
        {'max_loading_ratio', 'max_branch_loading', 'max_loading'});
    scenarios(idx).cascade_generations = first_available_numeric(raw_result, idx, ...
        {'cascade_generations', 'cascade_generation', 'generations'});
    scenarios(idx).tripped_branch_ids = first_available_vector(raw_result, idx, ...
        {'tripped_branch_ids', 'tripped_branches', 'failed_branches', 'branch_outages'});
end

payload = struct();
payload.metadata = metadata;
payload.scenarios = scenarios;

output_directory = fileparts(output_file);
if ~isempty(output_directory) && ~exist(output_directory, 'dir')
    mkdir(output_directory);
end

encoded = jsonencode(payload);
file_id = fopen(output_file, 'w');
if file_id < 0
    error('Could not open output file: %s', output_file);
end
cleanup = onCleanup(@() fclose(file_id));
fprintf(file_id, '%s\n', encoded);

fprintf('Saved AC-CFM validation fixture to %s\n', output_file);
fprintf('MATPOWER branch  Python branch  Unserved MW\n');
for idx = 1:numel(scenarios)
    fprintf('%15d  %13d  %11.3f\n', ...
        scenarios(idx).matpower_branch_id, ...
        scenarios(idx).python_branch_id, ...
        scenarios(idx).unserved_load_mw);
end
end

function scenario = empty_scenario()
scenario = struct();
scenario.scenario_id = NaN;
scenario.contingency_key = '';
scenario.matpower_branch_id = NaN;
scenario.python_branch_id = NaN;
scenario.unserved_load_mw = NaN;
scenario.max_loading_ratio = NaN;
scenario.cascade_generations = NaN;
scenario.tripped_branch_ids = [];
end

function value = first_available_numeric(result, index, field_names)
value = NaN;
for field_index = 1:numel(field_names)
    candidate = numeric_field(result, field_names{field_index}, index);
    if ~isnan(candidate)
        value = candidate;
        return
    end
end
end

function value = numeric_field(result, field_name, index)
value = NaN;
if ~isstruct(result) || ~isfield(result, field_name)
    return
end
field_value = result.(field_name);
try
    if isnumeric(field_value)
        value = double(field_value(index));
    elseif iscell(field_value) && isnumeric(field_value{index})
        cell_value = field_value{index};
        if ~isempty(cell_value)
            value = double(cell_value(1));
        end
    end
catch
    value = NaN;
end
end

function values = first_available_vector(result, index, field_names)
values = [];
for field_index = 1:numel(field_names)
    values = vector_field(result, field_names{field_index}, index);
    if ~isempty(values)
        return
    end
end
end

function values = vector_field(result, field_name, index)
values = [];
if ~isstruct(result) || ~isfield(result, field_name)
    return
end
field_value = result.(field_name);
try
    if iscell(field_value)
        values = field_value{index};
    elseif isnumeric(field_value)
        values = field_value(index, :);
    end
    values = values(:)';
catch
    values = [];
end
end

function commit = current_git_commit()
[status, output] = system('git rev-parse --short HEAD');
if status == 0
    commit = strtrim(output);
else
    commit = 'unknown';
end
end
