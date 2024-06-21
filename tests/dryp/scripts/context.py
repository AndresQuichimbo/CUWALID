import os
import sys
# Add the root of the CUWALID package to sys.path
package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, package_root)


from CUWALID.models.DRYP import dryp