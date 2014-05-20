from pipu import config

class Config(config.AbstractConfig):

    environments = {

        'production': {
            # Data directories
            'ACTIVE_RUNS_ROOT_DIRECTORY': '/srv/gs1/projects/scg/Runs',
            'ANALYSIS_ROOT_DIRECTORY': '/srv/gs1/projects/scg/Analysis',
            'RESULTS_ROOT_DIRECTORY': '/srv/gs1/projects/scg/Archive',
            'COMPLETED_RUNS_ROOT_DIRECTORY': '/srv/gs1/projects/scg/CompletedRuns',
            'GENOMES_ROOT_DIRECTORY': '/srv/gs1/projects/scg/Genomes',
            # LIMS-related settings
            'LIMS_HOST': 'nummel.stanford.edu',
            'RAKE_COMMAND': '/opt/scg/apps/rubygems/gems/1.8/bin/rake',
            'RAKE_FILE': '/opt/scg/uhts-archive/current/Rakefile',
            'RAILS_ENV': 'production',
            'LIMS_MODULE': 'utils.lims_adapter',

            # pipu settings
            'JOB_MANAGER': 'sjm',
            # Notification
            'MAIL': 'scg-auto-notify@lists.stanford.edu',

            'BWA_VERSION': 'BWA-0.7.4',
            },

        'staging': {
            # Data directories
            'ACTIVE_RUNS_ROOT_DIRECTORY': '/srv/gs1/projects/scg/Runs',
            'ANALYSIS_ROOT_DIRECTORY': '/srv/gs1/projects/scg/Analysis',
            'RESULTS_ROOT_DIRECTORY': '/srv/gs1/projects/scg/Archive/Staging',
            'COMPLETED_RUNS_ROOT_DIRECTORY':
            '/srv/gs1/projects/scg/CompletedRuns/Staging',
            'GENOMES_ROOT_DIRECTORY': '/srv/gs1/projects/scg/Genomes',

            # LIMS-related settings
            'LIMS_HOST': 'nummel.stanford.edu',
            'RAKE_COMMAND': '/opt/scg/apps/rubygems/gems/1.8/bin/rake',
            'RAKE_FILE': '/opt/scg/uhts-archive/current/Rakefile',
            'RAILS_ENV': 'production',
            'LIMS_MODULE': 'utils.lims_adapter',

            # pipu settings
            'JOB_MANAGER': 'sjm',
            # Notification
            'MAIL': 'scg-auto-notify@lists.stanford.edu',

            'BWA_VERSION': 'BWA-0.7.4',
            },

        'development' : {
            # Data directories
            'ACTIVE_RUNS_ROOT_DIRECTORY': '/data/Runs',
            'ANALYSIS_ROOT_DIRECTORY': '/data/Analysis',
            'RESULTS_ROOT_DIRECTORY': '/data/Results',
            'COMPLETED_RUNS_ROOT_DIRECTORY': '/data/CompletedRuns',
            'GENOMES_ROOT_DIRECTORY': '/data/Genomes',

            # LIMS-related settings
            'LIMS_HOST': 'nummel.stanford.edu',
            'RAKE_COMMAND': '/opt/scg/apps/rubygems/gems/1.8/bin/rake',
            'RAKE_FILE': '/opt/scg/uhts-archive/current/Rakefile',
            'RAILS_ENV': 'production',
            'LIMS_MODULE': 'utils.test_lims_adapter',

            # pipu settings
            'JOB_MANAGER': 'bpipe',
            # Notification
            'MAIL': None,

            'BWA_VERSION': 'BWA-0.7.4',
            }
        }
